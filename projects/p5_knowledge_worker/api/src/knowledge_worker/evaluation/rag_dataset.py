"""Bilingual RAG dataset (v2): documents with a train/test split, and graded queries.

Layout of a dataset folder:

    manifest.json     {"name", "version", "documents": [DocumentEntry, ...]}
    queries.jsonl     one DatasetQuery per line

Compared with eval_dataset.json (v1), labels name an exact section (and page for PDFs)
instead of a loose heading match, follow-up questions carry their conversation history, and
every document belongs to exactly one split so training data can't leak into the test set.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from knowledge_worker.text.normalize import normalize_text

Split = Literal["train", "test"]
QueryLanguage = Literal["en", "bn", "banglish", "mixed"]
Category = Literal[
    "english",
    "bangla",
    "banglish",
    "cross_lingual",
    "exact_term",
    "numeric",
    "table",
    "follow_up",
    "unanswerable",
]


def _stored(value: str | None) -> str | None:
    """Normalize like ingestion does (NFC, which decomposes e.g. Bangla U+09DF), so labels
    compare equal to stored headings."""
    return normalize_text(value) if value is not None else None


class DocumentEntry(BaseModel):
    """A source document. `path` is relative to the dataset folder."""

    name: str = Field(description="Filename as uploaded; labels refer to documents by this")
    path: str
    split: Split
    language: Literal["en", "bn", "mixed"]
    license: str = Field(min_length=1, description="e.g. CC-BY-4.0, CC-BY-SA-4.0, proprietary")
    source: str = Field(min_length=1, description="Where it came from, or 'synthetic'")
    publishable: bool = Field(
        description="May be redistributed with the dataset (false for e.g. news articles)"
    )


class RelevantSection(BaseModel):
    """A passage that answers the query.

    `section` is the exact heading as the parser produces it, or null for a document with no
    headings (then the whole document is the unit). `page` narrows PDFs to one page.
    """

    doc: str
    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    grade: int = Field(ge=1, le=3, description="3 answers it, 2 essential context, 1 related")

    _normalize = field_validator("section")(_stored)


class DatasetQuery(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")
    query: str = Field(min_length=1, max_length=1000)
    language: QueryLanguage
    category: Category
    answerable: bool
    history: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Earlier (question, answer) turns, oldest first. The answers are the "
        "reference ('gold') answers, so follow-ups are scored on this turn alone.",
    )
    relevant: list[RelevantSection] = Field(default_factory=list)
    answer: str | None = Field(default=None, description="Short reference answer")
    split: Split
    notes: str | None = None

    @model_validator(mode="after")
    def _consistent(self) -> DatasetQuery:
        if (self.category == "unanswerable") == self.answerable:
            raise ValueError("category 'unanswerable' must go with answerable=false, and only it")
        if self.answerable and not self.relevant:
            raise ValueError("an answerable query needs at least one relevant section")
        if self.answerable and not self.answer:
            raise ValueError("an answerable query needs a reference answer")
        if not self.answerable and self.relevant:
            raise ValueError("an unanswerable query can't have relevant sections")
        if (self.category == "follow_up") != bool(self.history):
            raise ValueError("follow_up queries need history, and only they have it")
        return self


class Manifest(BaseModel):
    name: str
    version: str
    documents: list[DocumentEntry]


class RagDataset(BaseModel):
    root: Path
    manifest: Manifest
    queries: list[DatasetQuery]

    def document(self, name: str) -> DocumentEntry | None:
        return next((d for d in self.manifest.documents if d.name == name), None)

    def split(self, split: Split) -> list[DatasetQuery]:
        return [q for q in self.queries if q.split == split]


def load_rag_dataset(root: str | Path) -> RagDataset:
    """Read manifest.json and queries.jsonl. Schema errors name the offending line."""
    root = Path(root)
    manifest = Manifest.model_validate_json((root / "manifest.json").read_text(encoding="utf-8"))
    queries: list[DatasetQuery] = []
    lines = (root / "queries.jsonl").read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            queries.append(DatasetQuery.model_validate(json.loads(line)))
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"queries.jsonl line {number}: {exc}") from exc
    return RagDataset(root=root, manifest=manifest, queries=queries)
