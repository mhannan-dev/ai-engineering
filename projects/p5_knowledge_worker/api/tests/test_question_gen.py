"""Step C: draft eval questions with an LLM and filter weak drafts."""

import pytest

from knowledge_worker.evaluation.question_gen import (
    GeneratedQuestion,
    GeneratedQuestions,
    build_messages,
    generate_candidates,
    keep_candidate,
    overlap_ratio,
    target_language,
)
from knowledge_worker.evaluation.rag_dataset import DatasetQuery, DocumentEntry

EN_DOC = DocumentEntry(
    name="hr.md", path="hr.md", split="train", language="en",
    license="CC-BY-4.0", source="synthetic", publishable=True,
)
BN_DOC = EN_DOC.model_copy(update={"name": "travel_bn.md", "language": "bn", "split": "test"})

PASSAGE = (
    "Every full-time employee receives 20 working days of paid annual leave per calendar year. "
    "Annual leave is requested in the HR portal under the code LV-ANN."
)
BN_PASSAGE = "ঢাকার বাইরে কোনো জেলা সদরে গেলে প্রতিদিন ১,৫০০ টাকা দৈনিক ভাতা পাওয়া যাবে।"


class FakeLLM:
    def __init__(self, questions=None, error=None):
        self.questions = questions or []
        self.error = error
        self.messages = None

    def generate_structured(self, messages, response_model, temperature=0.0, max_tokens=1500):
        self.messages = messages
        if self.error:
            raise self.error
        assert response_model is GeneratedQuestions
        return GeneratedQuestions(questions=[GeneratedQuestion(question=q, answer=a) for q, a in self.questions])


def draft(**overrides) -> DatasetQuery:
    base = {
        "id": "x-01", "query": "How much paid holiday do staff get each year?", "language": "en",
        "category": "english", "answerable": True,
        "relevant": [{"doc": "hr.md", "section": "1. Annual leave", "grade": 3}],
        "answer": "20 working days", "split": "train",
    }
    return DatasetQuery.model_validate({**base, **overrides})


class TestTargetLanguage:
    @pytest.mark.parametrize(
        "category,doc_language,expected",
        [
            ("english", "bn", "en"),
            ("bangla", "en", "bn"),
            ("banglish", "en", "banglish"),
            ("cross_lingual", "en", "bn"),
            ("cross_lingual", "bn", "en"),
            ("cross_lingual", "mixed", "bn"),  # mixed counts as English
            ("exact_term", "bn", "bn"),
            ("numeric", "en", "en"),
            ("table", "mixed", "en"),
        ],
    )
    def test_language_per_category(self, category, doc_language, expected):
        assert target_language(category, doc_language) == expected

    @pytest.mark.parametrize("category", ["follow_up", "unanswerable"])
    def test_hand_written_categories_are_rejected(self, category):
        with pytest.raises(ValueError):
            target_language(category, "en")


class TestBuildMessages:
    def test_has_system_and_user_messages(self):
        messages = build_messages("english", EN_DOC, "1. Annual leave", PASSAGE, 3)
        assert [m["role"] for m in messages] == ["system", "user"]

    def test_user_message_carries_the_section_count_and_language(self):
        user = build_messages("cross_lingual", EN_DOC, "1. Annual leave", PASSAGE, 3)[-1]["content"]
        assert "1. Annual leave" in user
        assert PASSAGE in user
        assert "3" in user
        assert "Bangla" in user  # cross_lingual on an English document asks for Bangla

    @pytest.mark.parametrize("category,name", [("banglish", "Banglish"), ("english", "English")])
    def test_names_the_target_language(self, category, name):
        user = build_messages(category, EN_DOC, None, PASSAGE, 2)[-1]["content"]
        assert name in user

    def test_categories_get_different_instructions(self):
        prompts = {
            c: "\n".join(m["content"] for m in build_messages(c, EN_DOC, "h", PASSAGE, 2))
            for c in ("english", "exact_term", "numeric", "table")
        }
        assert len(set(prompts.values())) == len(prompts)


class TestGenerateCandidates:
    def test_turns_llm_output_into_dataset_queries(self):
        llm = FakeLLM([("  How much paid\n holiday do I get?  ", " 20 working days "), ("What code books leave?", "LV-ANN")])
        out = generate_candidates(llm, EN_DOC, "1. Annual leave", PASSAGE, "english", 5, "en-hr")
        assert [q.id for q in out] == ["en-hr-01", "en-hr-02"]
        first = out[0]
        assert first.query == "How much paid holiday do I get?"
        assert first.answer == "20 working days"
        assert (first.language, first.category, first.split, first.answerable) == ("en", "english", "train", True)
        assert [(r.doc, r.section, r.grade) for r in first.relevant] == [("hr.md", "1. Annual leave", 3)]
        assert llm.messages is not None, "the prompt comes from build_messages"

    def test_drops_empty_items_and_caps_at_n(self):
        llm = FakeLLM([("", "x"), ("Q one?", ""), ("Q two?", "a"), ("Q three?", "b"), ("Q four?", "c")])
        out = generate_candidates(llm, EN_DOC, "h", PASSAGE, "english", 2, "p")
        assert [q.query for q in out] == ["Q two?", "Q three?"]
        assert [q.id for q in out] == ["p-01", "p-02"]

    def test_split_and_language_follow_the_document(self):
        llm = FakeLLM([("What is the daily allowance outside Dhaka?", "1,500 taka")])
        out = generate_candidates(llm, BN_DOC, "২. দৈনিক ভাতার হার", BN_PASSAGE, "cross_lingual", 1, "xl")
        assert (out[0].split, out[0].language) == ("test", "en")

    def test_llm_failure_returns_nothing(self):
        assert generate_candidates(FakeLLM(error=RuntimeError("down")), EN_DOC, "h", PASSAGE, "english", 3, "p") == []


class TestOverlapRatio:
    def test_identical_and_disjoint(self):
        assert overlap_ratio("annual leave days", "annual leave days") == pytest.approx(1.0)
        assert overlap_ratio("zebra quantum", PASSAGE) == 0.0

    def test_stemming_and_stopwords(self):
        # "leaves" stems like "leave"; "the" and "of" are stopwords and don't count.
        assert overlap_ratio("the leaves of zebra", "annual leave") == pytest.approx(0.5)

    def test_bangla(self):
        assert overlap_ratio("দৈনিক ভাতা কত", BN_PASSAGE) > 0.5

    def test_no_terms(self):
        assert overlap_ratio("the of a", PASSAGE) == 0.0


class TestKeepCandidate:
    def test_keeps_a_good_paraphrase(self):
        assert keep_candidate(draft(), PASSAGE) == (True, "")

    def test_rejects_a_copy_of_the_passage(self):
        keep, reason = keep_candidate(draft(query="Every full-time employee receives paid annual leave per calendar year?"), PASSAGE)
        assert not keep and "cop" in reason

    def test_exact_term_may_reuse_the_passage_words(self):
        # Copied wording (overlap 0.88) is fine when the point is the exact term itself.
        copied = "Which code is annual leave requested under in the HR portal?"
        assert keep_candidate(draft(query=copied, category="exact_term", answer="LV-ANN"), PASSAGE)[0]
        assert not keep_candidate(draft(query=copied, answer="LV-ANN"), PASSAGE)[0]

    def test_rejects_a_number_not_in_the_passage(self):
        keep, reason = keep_candidate(draft(answer="25 working days"), PASSAGE)
        assert not keep and "number" in reason

    @pytest.mark.parametrize("answer", ["১৫০০ টাকা", "1500 taka", "১,৫০০ টাকা"])
    def test_numbers_match_across_digits_and_separators(self, answer):
        # Passage has "১,৫০০". Overlap of this paraphrase is 0.33, so only the number rule applies.
        q = draft(query="শহরের বাইরে গেলে রোজ কত পাব?", language="bn", category="bangla",
                  answer=answer, relevant=[{"doc": "travel_bn.md", "section": "s", "grade": 3}])
        assert keep_candidate(q, BN_PASSAGE) == (True, "")

    @pytest.mark.parametrize(
        "language,question",
        [("bn", "How much leave do I get?"), ("en", "ছুটি কত দিন?"), ("banglish", "chuti কত din?")],
    )
    def test_rejects_wrong_script(self, language, question):
        keep, reason = keep_candidate(draft(query=question, language=language), PASSAGE)
        assert not keep and "script" in reason
