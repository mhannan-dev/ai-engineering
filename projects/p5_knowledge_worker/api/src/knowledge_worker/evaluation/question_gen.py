"""Draft eval questions from document sections with an LLM, then filter the weak ones.

The drafts are candidates for human review (step D), never added to the dataset directly.

    section text ──► build_messages ──► LLM ──► generate_candidates ──► keep_candidate ──► review
"""

from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

from knowledge_worker.evaluation.rag_dataset import (
    Category,
    DatasetQuery,
    DocumentEntry,
    QueryLanguage,
)
from knowledge_worker.generation.llm import LLMClient
from knowledge_worker.text.tokenizer import tokenize

logger = logging.getLogger(__name__)

LANGUAGE_NAMES: dict[QueryLanguage, str] = {
    "en": "English",
    "bn": "Bangla",
    "banglish": "Banglish",
    "mixed": "English",
}

SYSTEM_PROMPT = """You write evaluation questions for a document search system used by employees in Bangladesh.

Each question must:
- be answerable from the given section alone, with a short answer taken from it;
- sound like a real user who has NOT read the document: use your own words, not the section's
  phrasing, and don't mention "the section", "the passage" or "the document";
- be self-contained (no "it", "this policy" without saying which);
- differ from the other questions in what it asks.

Return only questions you are confident about; fewer good questions beat more weak ones."""

# What makes a useful question for each category, beyond the shared rules.
CATEGORY_INSTRUCTIONS: dict[Category, str] = {
    "english": "Ask everyday questions about the facts, rules or conditions in the section.",
    "bangla": "Ask everyday questions about the facts, rules or conditions in the section.",
    "banglish": (
        "Write Bangla as people type it in chat, in Latin letters (e.g. 'chuti koto din?', "
        "'office kokhon khola thake?'). Never use Bangla script."
    ),
    "cross_lingual": (
        "The section is in a different language from the questions. Translate the meaning, "
        "not the words: ask as a speaker of the question language naturally would."
    ),
    "exact_term": (
        "Ask about a specific code, form ID, name, extension or other identifier in the "
        "section, and include that identifier in the question (e.g. 'What is LV-SCK used for?')."
    ),
    "numeric": (
        "Ask about a number in the section: an amount, limit, duration, count or date. The "
        "answer must contain that number exactly as written."
    ),
    "table": (
        "Ask about a specific row or cell of the table in the section, the way someone looking "
        "for one value would (e.g. 'What happens on day 2?')."
    ),
}

_BANGLA_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_THOUSANDS = re.compile(r"(?<=\d),(?=\d{3})")
_NUMBER = re.compile(r"\d+(?:\.\d+)?")

# Categories this generator drafts. follow_up needs a conversation and unanswerable needs
# questions about things the documents don't contain, so both are written by hand.
GENERATED_CATEGORIES: tuple[Category, ...] = (
    "english",
    "bangla",
    "banglish",
    "cross_lingual",
    "exact_term",
    "numeric",
    "table",
)


class GeneratedQuestion(BaseModel):
    question: str
    answer: str = Field(description="Short answer taken from the passage")


class GeneratedQuestions(BaseModel):
    """The structured output requested from the LLM."""

    questions: list[GeneratedQuestion]


def target_language(category: Category, doc_language: str) -> QueryLanguage:
    """The language a drafted question should be written in.

    - english -> "en", bangla -> "bn", banglish -> "banglish"
    A "mixed" document counts as "en" for the two rules below:
    - cross_lingual -> the other language than the document: "en" (or "mixed") documents
      get "bn" questions, "bn" documents get "en" questions
    - exact_term, numeric, table -> the document's own language

    Raises:
        ValueError: for follow_up and unanswerable, which aren't generated.
    """
    if category not in GENERATED_CATEGORIES:
        raise ValueError(f"{category!r} questions are written by hand, not generated")
    if category == "english":
        return "en"
    if category == "bangla":
        return "bn"
    if category == "banglish":
        return "banglish"
    own: QueryLanguage = "bn" if doc_language == "bn" else "en"
    if category == "cross_lingual":
        return "en" if own == "bn" else "bn"
    return own


def build_messages(
    category: Category, doc: DocumentEntry, heading: str | None, text: str, n: int
) -> list[dict[str, str]]:
    """The chat messages asking for `n` questions of `category` about one section.

    Returns a system message and a user message. The user message must contain the heading
    (when there is one), the section text, the number of questions, and the target language
    by name ("English", "Bangla" or "Banglish"). What makes a good question for each category
    is up to you; see the spec in the task description.
    """
    language = LANGUAGE_NAMES[target_language(category, doc.language)]
    title = f"Section heading: {heading}\n" if heading else ""
    user = (
        f"{title}Section text:\n\"\"\"\n{text}\n\"\"\"\n\n"
        f"Write up to {n} questions in {language}, each with a short answer from the section "
        f"(the answer may stay in the section's language).\n"
        f"{CATEGORY_INSTRUCTIONS[category]}"
    )
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def generate_candidates(
    llm: LLMClient,
    doc: DocumentEntry,
    heading: str | None,
    text: str,
    category: Category,
    n: int,
    id_prefix: str,
) -> list[DatasetQuery]:
    """Ask the LLM for questions about one section and turn them into dataset queries.

    Each query is answerable, labels this section with grade 3, takes its split from `doc`,
    and gets id f"{id_prefix}-{i:02d}" numbered from 1 in output order. Whitespace is tidied,
    empty questions or answers are dropped, and at most `n` are returned.

    An LLM failure returns [] (and logs), so one bad section doesn't stop a batch run.
    """
    language = target_language(category, doc.language)
    try:
        result = llm.generate_structured(
            messages=build_messages(category, doc, heading, text, n),
            response_model=GeneratedQuestions,
            temperature=0.7,  # some variety between drafts; review catches the misses
            max_tokens=1200,
        )
    except Exception:
        logger.warning("Question generation failed for %s / %s", doc.name, heading, exc_info=True)
        return []

    queries: list[DatasetQuery] = []
    for item in result.questions:
        question, answer = " ".join(item.question.split()), " ".join(item.answer.split())
        if not question or not answer:
            continue
        queries.append(
            DatasetQuery(
                id=f"{id_prefix}-{len(queries) + 1:02d}",
                query=question,
                language=language,
                category=category,
                answerable=True,
                relevant=[{"doc": doc.name, "section": heading, "grade": 3}],
                answer=answer,
                split=doc.split,
            )
        )
        if len(queries) == n:
            break
    return queries


def overlap_ratio(question: str, passage: str) -> float:
    """Share of the question's distinct content terms that also appear in the passage, 0..1.

    Uses the project tokenizer (stopwords removed, stemmed, Bangla digits as ASCII), so
    "leave" and "leaves" count as the same term. A question with no terms gives 0.0.
    """
    terms = set(tokenize(question))
    if not terms:
        return 0.0
    return len(terms & set(tokenize(passage))) / len(terms)


def _numbers(text: str) -> set[str]:
    """Numbers as ASCII digit strings, with Bangla digits mapped and "1,500" read as 1500."""
    return set(_NUMBER.findall(_THOUSANDS.sub("", text.translate(_BANGLA_DIGITS))))


def _has_bangla(text: str) -> bool:
    return any("ঀ" <= ch <= "৿" for ch in text)


def keep_candidate(query: DatasetQuery, passage: str, max_overlap: float = 0.6) -> tuple[bool, str]:
    """Decide whether a drafted query is worth sending to review. Returns (keep, reason).

    Reject, with a short reason, when:
    - the question copies the passage: overlap_ratio > max_overlap (LLM drafts tend to reuse
      the passage's words, which makes BM25 look better than it is on real questions);
      exact_term is exempt from this rule (why?)
    - the answer has a number that isn't in the passage (a hallucinated figure). Compare
      numbers as digit runs after mapping Bangla digits to ASCII and dropping thousands
      separators, so "১,৫০০" in the passage matches "1500" in the answer. Don't use the
      tokenizer for this: it splits "1,500" at the comma.
    - the script doesn't match `query.language`: "bn" needs Bangla script, "en" and
      "banglish" must have none

    Otherwise return (True, "").
    """
    # exact_term questions must name the identifier, so sharing the passage's words is the
    # point there. (cross_lingual needs no exemption: its words can't overlap the passage.)
    if query.category != "exact_term":
        ratio = overlap_ratio(query.query, passage)
        if ratio > max_overlap:
            return False, f"copies the passage ({ratio:.0%} of its terms)"

    invented = _numbers(query.answer or "") - _numbers(passage)
    if invented:
        return False, f"answer has a number not in the passage: {', '.join(sorted(invented))}"

    if (query.language == "bn") != _has_bangla(query.query):
        expected = "Bangla" if query.language == "bn" else "Latin"
        return False, f"script doesn't match language {query.language!r} (expected {expected})"
    return True, ""
