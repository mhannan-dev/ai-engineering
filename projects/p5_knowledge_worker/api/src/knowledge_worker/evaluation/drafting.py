"""Batch drafting and review workflow for the v2 dataset.

    # 1. Draft questions for every document (or --docs ...) into drafts.jsonl
    uv run python -m knowledge_worker.evaluation.drafting draft ../datasets/bilingual_rag_eval
    # 2. Review drafts.jsonl: set "status" to "accept" or "reject", edit "query"/"answer" freely
    # 3. Append accepted drafts to queries.jsonl (only if the result validates)
    uv run python -m knowledge_worker.evaluation.drafting merge ../datasets/bilingual_rag_eval

`draft --dry-run` lists the planned LLM calls without making any.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from knowledge_worker.evaluation.question_gen import generate_candidates, keep_candidate
from knowledge_worker.evaluation.rag_dataset import (
    Category,
    DatasetQuery,
    DocumentEntry,
    RagDataset,
    load_rag_dataset,
)
from knowledge_worker.evaluation.validate import validate_dataset
from knowledge_worker.generation.llm import LLMClient
from knowledge_worker.ingestion.parsers import parse_document
from knowledge_worker.services.document_service import detect_format

DRAFTS_FILE = "drafts.jsonl"
MIN_SECTION_CHARS = 80
# Disclaimers at the top of the synthetic documents say nothing worth asking about.
DEFAULT_SKIP = r"(?i)synthetic retrieval-test document|কাল্পনিক নথি"
_CODE = re.compile(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)+\b|\b[A-Z]-\d+\b")
_DIGIT = re.compile(r"[0-9০-৯]")
REVIEW_FIELDS = ("status", "keep", "reason", "passage")


@dataclass(frozen=True)
class Job:
    doc: DocumentEntry
    section_index: int
    heading: str | None
    text: str
    category: Category


def categories_for(doc: DocumentEntry, text: str) -> list[Category]:
    """Which categories are worth drafting for a section, judged from its content."""
    native: Category = "bangla" if doc.language == "bn" else "english"
    chosen: list[Category] = [native, "cross_lingual"]
    if doc.language == "bn":
        chosen.append("banglish")
    if _DIGIT.search(text):
        chosen.append("numeric")
    if _CODE.search(text):
        chosen.append("exact_term")
    if sum(" | " in line for line in text.splitlines()) >= 2:  # DOCX table rows
        chosen.append("table")
    return chosen


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", Path(name).stem.lower()).strip("-") or "doc"


def plan(
    dataset: RagDataset,
    docs: list[str] | None = None,
    categories: list[Category] | None = None,
    skip: str = DEFAULT_SKIP,
) -> list[Job]:
    """One job per (section, category) to draft, in document order."""
    skip_re = re.compile(skip) if skip else None
    jobs: list[Job] = []
    for doc in dataset.manifest.documents:
        if docs and doc.name not in docs:
            continue
        data = (dataset.root / doc.path).read_bytes()
        for index, section in enumerate(parse_document(data, detect_format(doc.name, data)), start=1):
            if len(section.text) < MIN_SECTION_CHARS or (skip_re and skip_re.search(section.text)):
                continue
            for category in categories_for(doc, section.text):
                if categories and category not in categories:
                    continue
                jobs.append(Job(doc, index, section.heading, section.text, category))
    return jobs


def draft(llm: LLMClient, jobs: list[Job], per_section: int) -> list[dict]:
    """Run the jobs and return review records: the draft plus status, verdict and passage."""
    records: list[dict] = []
    for job in jobs:
        prefix = f"{job.doc.split}-{_slug(job.doc.name)}-s{job.section_index:02d}-{job.category.replace('_', '')}"
        for query in generate_candidates(
            llm, job.doc, job.heading, job.text, job.category, per_section, prefix
        ):
            keep, reason = keep_candidate(query, job.text)
            records.append({
                "status": "pending",
                "keep": keep,
                "reason": reason,
                **query.model_dump(mode="json"),
                "passage": job.text,
            })
    return records


@dataclass
class MergeResult:
    added: int = 0
    skipped_duplicates: int = 0
    pending: int = 0
    rejected: int = 0
    errors: list[str] | None = None


def merge(root: Path) -> MergeResult:
    """Append accepted drafts to queries.jsonl. Nothing is written unless the merged dataset
    validates, so a bad label in review can't break the dataset."""
    dataset = load_rag_dataset(root)
    existing = {q.id for q in dataset.queries}
    result = MergeResult()
    new: list[DatasetQuery] = []
    for line in (root / DRAFTS_FILE).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        status = record.get("status")
        if status == "pending":
            result.pending += 1
            continue
        if status != "accept":
            result.rejected += 1
            continue
        query = DatasetQuery.model_validate({k: v for k, v in record.items() if k not in REVIEW_FIELDS})
        if query.id in existing:
            result.skipped_duplicates += 1
            continue
        existing.add(query.id)
        new.append(query)

    merged = dataset.model_copy(update={"queries": [*dataset.queries, *new]})
    report = validate_dataset(merged)
    if report.errors:
        result.errors = report.errors
        return result
    with (root / "queries.jsonl").open("a", encoding="utf-8") as f:
        for query in new:
            f.write(json.dumps(query.model_dump(mode="json", exclude_none=True), ensure_ascii=False) + "\n")
    result.added = len(new)
    return result


def _llm() -> LLMClient:
    from knowledge_worker.config import get_settings
    from knowledge_worker.generation.llm import LiteLLMClient

    settings = get_settings()
    return LiteLLMClient(
        model=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY, api_base=settings.OPENAI_BASE_URL
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Draft and merge eval questions")
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("draft", help="Draft questions into drafts.jsonl")
    d.add_argument("root")
    d.add_argument("--docs", nargs="*", help="Document names (default: all)")
    d.add_argument("--categories", nargs="*", help="Limit to these categories")
    d.add_argument("--per-section", type=int, default=2)
    d.add_argument("--dry-run", action="store_true", help="Show the plan; no LLM calls")
    m = sub.add_parser("merge", help="Append accepted drafts to queries.jsonl")
    m.add_argument("root")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    root = Path(args.root)

    if args.command == "merge":
        result = merge(root)
        if result.errors:
            print("Not merged; the dataset would be invalid:")
            for error in result.errors:
                print(f"  ERROR {error}")
            return 1
        print(f"added {result.added}, duplicates skipped {result.skipped_duplicates}, "
              f"still pending {result.pending}, rejected {result.rejected}")
        return 0

    jobs = plan(load_rag_dataset(root), args.docs, args.categories)
    by_category = Counter(j.category for j in jobs)
    print(f"{len(jobs)} LLM calls: " + ", ".join(f"{c} {n}" for c, n in sorted(by_category.items())))
    if args.dry_run:
        return 0
    out = root / DRAFTS_FILE
    if out.exists():
        print(f"{out} exists; review and merge it (or delete it) before drafting again.")
        return 1
    records = draft(_llm(), jobs, args.per_section)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    kept = sum(r["keep"] for r in records)
    print(f"wrote {len(records)} drafts to {out} ({kept} pass the filters, "
          f"{len(records) - kept} flagged). Set each 'status' to accept or reject, then merge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
