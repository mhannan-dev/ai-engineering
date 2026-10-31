"""Prompts and context formatting for faithful RAG generation."""

from collections.abc import Sequence

from knowledge_worker.retrieval.models import RerankedChunk, RetrievedChunk

SYSTEM_PROMPT = """You are an enterprise knowledge assistant. Answer the user's question faithfully using ONLY the provided document passages.

CITATION RULES:
1. Every factual sentence or claim MUST be followed immediately by a bracketed citation pointing to its source.
   - If the source has a page number: [filename.pdf, Page N]
   - If the source has a section heading: [filename.md, Section Heading]
   - If neither: [filename.ext]
2. Cite ONLY documents that appear in the provided context passages. NEVER invent or hallucinate filenames or page numbers.
3. If two facts come from different passages, cite each fact separately with its own bracketed citation.

FAITHFULNESS & ABSTENTION:
1. Answer ONLY what is directly supported by the context passages. Do not extrapolate, assume, or use prior knowledge.
2. If the passages do not contain enough facts to answer the question, state clearly:
   - In English: "The provided documents do not contain enough information to answer this question."
   - In Bangla: "প্রদত্ত নথিপত্রে এই প্রশ্নের উত্তর দেওয়ার জন্য পর্যাপ্ত তথ্য পাওয়া যায়নি।"
   Explain what specific information is missing.

LANGUAGE POLICY:
- If the user query is in Bangla (বাংলা) or Banglish (Romanized Bengali, e.g. "kobe chuti pabo"), answer fluently and naturally in standard Bengali script (বাংলা হরফে).
- If the user query is in English, answer in English.
"""


def format_context_passages(chunks: Sequence[RerankedChunk | RetrievedChunk]) -> str:
    """Format retrieved passages into a clean, structured context block."""
    if not chunks:
        return "No relevant passages found in the knowledge base."

    blocks: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        page_str = f"Page {chunk.page}" if chunk.page is not None else "N/A"
        heading_str = chunk.heading if chunk.heading else "N/A"
        score_str = f" (relevance: {chunk.score:.3f})" if hasattr(chunk, "score") else ""

        block = (
            f"--- PASSAGE {i}{score_str} ---\n"
            f"Source Document: {chunk.document_filename}\n"
            f"Page: {page_str}\n"
            f"Section: {heading_str}\n"
            f"Content:\n{chunk.text.strip()}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def build_user_prompt(
    query: str,
    chunks: Sequence[RerankedChunk | RetrievedChunk],
    normalized_query: str | None = None,
    was_banglish: bool = False,
) -> str:
    """Construct user prompt combining context passages and the user's question."""
    passages_text = format_context_passages(chunks)

    query_note = ""
    if was_banglish and normalized_query:
        query_note = f"\n(Note: User query was detected as Banglish; Bengali normalized form: '{normalized_query}')"

    return (
        f"Context Passages:\n"
        f"================\n"
        f"{passages_text}\n"
        f"================\n\n"
        f"User Question: {query}{query_note}\n\n"
        f"Please provide a faithful, well-cited answer based strictly on the context passages above."
    )


REWRITE_SYSTEM_PROMPT = """You turn the user's latest chat message into a standalone question for a document search engine.

Use the conversation only to resolve what the latest message refers to ("it", "that policy", "and sick leave?", "what about Chattogram?").

Rules:
- Keep the language and script of the latest message: Bangla stays Bangla, Banglish stays Banglish, English stays English.
- Keep codes, numbers, names and quoted terms exactly as written.
- If the latest message is already a complete question, return it unchanged.
- Do not answer the question, and do not add facts that are not in the conversation.
- Return one question only."""


def build_rewrite_prompt(
    history: Sequence[tuple[str, str]], question: str, max_answer_chars: int = 600
) -> str:
    """The recent (question, answer) turns, oldest first, then the message to rewrite.

    Answers are cut to `max_answer_chars`: resolving a reference needs the topic, not the
    whole answer, and long answers would cost tokens on every follow-up.
    """
    lines = ["Conversation so far:"]
    for asked, answered in history:
        if len(answered) > max_answer_chars:
            answered = answered[:max_answer_chars].rstrip() + " …"
        lines.append(f"User: {asked}")
        lines.append(f"Assistant: {answered}")
    lines.append("")
    lines.append(f"Latest message: {question}")
    lines.append("")
    lines.append("Standalone question:")
    return "\n".join(lines)
