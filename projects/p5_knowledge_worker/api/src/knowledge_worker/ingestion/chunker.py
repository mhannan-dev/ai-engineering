"""Sentence-aware chunking with token budgets and overlap.

Sentences are packed greedily until the next one would exceed `max_tokens`; the next chunk then
starts with the trailing sentences that fit in `overlap_tokens`, so an answer that spans a chunk
boundary is still retrievable. Splits on Bangla danda (।) as well as . ! ?.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

from knowledge_worker.ingestion.parsers import Section

TokenCounter = Callable[[str], int]

_SENTENCE_END = re.compile(r"(?<=[.!?।॥])\s+|\n+")


@dataclass(frozen=True)
class Chunk:
    text: str
    token_count: int
    page: int | None
    heading: str | None


def approx_token_count(text: str) -> int:
    """Fallback when the model tokenizer is unavailable: ~4 chars/token, Bangla ~2 chars/token."""
    bengali = sum(0x0980 <= ord(c) <= 0x09FF for c in text)
    return max(1, round(bengali / 2 + (len(text) - bengali) / 4))


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_END.split(text) if s.strip()]


def _split_long(sentence: str, max_tokens: int, count: TokenCounter) -> list[str]:
    """Break a sentence longer than the budget on word boundaries."""
    pieces, current = [], []
    for word in sentence.split():
        candidate = " ".join([*current, word])
        if current and count(candidate) > max_tokens:
            pieces.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        pieces.append(" ".join(current))
    return pieces


def chunk_sections(
    sections: list[Section],
    max_tokens: int = 400,
    overlap_tokens: int = 60,
    count: TokenCounter = approx_token_count,
) -> list[Chunk]:
    if overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be smaller than max_tokens")

    chunks: list[Chunk] = []
    for section in sections:
        sentences: list[tuple[str, int]] = []
        for sentence in split_sentences(section.text):
            n = count(sentence)
            if n > max_tokens:
                sentences.extend((p, count(p)) for p in _split_long(sentence, max_tokens, count))
            else:
                sentences.append((sentence, n))

        window: list[tuple[str, int]] = []
        window_tokens = 0
        fresh = 0  # sentences in the window not already emitted in the previous chunk

        def emit() -> None:
            text = " ".join(s for s, _ in window)
            chunks.append(Chunk(text, count(text), section.page, section.heading))

        for sentence, n in sentences:
            if window and window_tokens + n > max_tokens:
                emit()
                # Carry trailing sentences forward as overlap.
                carried, carried_tokens = [], 0
                for s, sn in reversed(window):
                    if carried_tokens + sn > overlap_tokens or carried_tokens + sn + n > max_tokens:
                        break
                    carried.insert(0, (s, sn))
                    carried_tokens += sn
                window, window_tokens, fresh = carried, carried_tokens, 0
            window.append((sentence, n))
            window_tokens += n
            fresh += 1
        if window and fresh:
            emit()
    return chunks
