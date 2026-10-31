"""Evaluation dataset schema and loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from knowledge_worker.text.normalize import normalize_text


def _as_stored(value: str | None) -> str | None:
    """Normalize a label the way ingestion normalizes chunk headings.

    Headings are stored after NFC normalization, which decomposes characters like Bangla
    'য়' (U+09DF) into 'য' + nukta. A label typed with the precomposed form looks identical
    but never matches, so labels go through the same normalization.
    """
    return normalize_text(value) if value is not None else None


class EvalRelevanceGrade(BaseModel):
    document_filename: str
    heading: str
    grade: int = Field(ge=0, le=3)

    _normalize_heading = field_validator("heading")(_as_stored)


class EvalQuery(BaseModel):
    id: str
    query: str
    category: Literal["english", "bangla", "cross_lingual", "banglish", "unanswerable"]
    is_answerable: bool = True
    expected_doc: str | None = None
    expected_heading: str | None = None
    expected_fact: str | None = None
    relevance_grades: list[EvalRelevanceGrade] = Field(default_factory=list)

    _normalize_heading = field_validator("expected_heading")(_as_stored)


def get_default_dataset_path() -> Path:
    """Resolve the default path to sample_documents/eval_dataset.json."""
    # From api/src/knowledge_worker/evaluation/dataset.py -> p5_knowledge_worker/sample_documents/eval_dataset.json
    here = Path(__file__).resolve()
    # parents: [evaluation, knowledge_worker, src, api, p5_knowledge_worker]
    root = here.parents[4]
    return root / "sample_documents" / "eval_dataset.json"


def load_eval_dataset(path: str | Path | None = None) -> list[EvalQuery]:
    """Load and validate the evaluation dataset from a JSON file.

    Args:
        path: Path to the JSON file. Defaults to sample_documents/eval_dataset.json.

    Returns:
        List of validated EvalQuery objects.
    """
    file_path = Path(path) if path is not None else get_default_dataset_path()
    if not file_path.exists():
        raise FileNotFoundError(f"Eval dataset not found at: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    return [EvalQuery.model_validate(item) for item in raw_data]

