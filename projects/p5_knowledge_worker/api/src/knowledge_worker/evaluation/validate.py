"""Check a v2 dataset beyond its schema: files, labels, leakage, language and balance.

    uv run python -m knowledge_worker.evaluation.validate ../datasets/bilingual_rag_eval

Exits with status 1 if there are errors. Warnings (thin categories, near-duplicates) don't
fail the run but are worth fixing before publishing.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from knowledge_worker.core.exceptions import AppException
from knowledge_worker.evaluation.rag_dataset import RagDataset, load_rag_dataset
from knowledge_worker.ingestion.parsers import ParseError, parse_document
from knowledge_worker.services.document_service import detect_format
from knowledge_worker.text.normalize import normalize_for_search

MIN_PER_CATEGORY = 20  # below this, one query moves a category's recall by 5 points or more


def _has_bangla(text: str) -> bool:
    return any("ঀ" <= ch <= "৿" for ch in text)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    counts: dict[str, Counter] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class _ParsedDoc:
    sections: set[str]
    pages: set[int]
    has_headings: bool


def _parse(dataset: RagDataset, report: Report) -> dict[str, _ParsedDoc]:
    parsed: dict[str, _ParsedDoc] = {}
    names = Counter(d.name for d in dataset.manifest.documents)
    for name, count in names.items():
        if count > 1:
            report.errors.append(f"document {name!r} is listed {count} times")
    for doc in dataset.manifest.documents:
        path = dataset.root / doc.path
        if not path.is_file():
            report.errors.append(f"document {doc.name!r}: file not found at {doc.path}")
            continue
        data = path.read_bytes()
        try:
            sections = parse_document(data, detect_format(doc.name, data))
        # ParseError for unusable text, UnsupportedFileError (an AppException) for the format.
        except (ParseError, AppException) as exc:
            report.errors.append(f"document {doc.name!r}: can't be parsed ({exc})")
            continue
        headings = {s.heading for s in sections if s.heading}
        parsed[doc.name] = _ParsedDoc(
            sections=headings,
            pages={s.page for s in sections if s.page is not None},
            has_headings=bool(headings),
        )
    return parsed


def _check_labels(dataset: RagDataset, parsed: dict[str, _ParsedDoc], report: Report) -> None:
    for q in dataset.queries:
        for rel in q.relevant:
            entry = dataset.document(rel.doc)
            if entry is None:
                report.errors.append(f"{q.id}: relevant doc {rel.doc!r} is not in the manifest")
                continue
            # Leakage: a query may only point at documents of its own split.
            if entry.split != q.split:
                report.errors.append(
                    f"{q.id}: {q.split} query labels {rel.doc!r}, which is in {entry.split}"
                )
            doc = parsed.get(rel.doc)
            if doc is None:
                continue  # already reported as unreadable
            if rel.section is None:
                if doc.has_headings:
                    report.errors.append(
                        f"{q.id}: {rel.doc!r} has headings, so the label needs an exact section"
                    )
            elif rel.section not in doc.sections:
                report.errors.append(
                    f"{q.id}: section {rel.section!r} not found in {rel.doc!r}"
                )
            if rel.page is not None and rel.page not in doc.pages:
                report.errors.append(f"{q.id}: page {rel.page} not found in {rel.doc!r}")


def _check_queries(dataset: RagDataset, report: Report) -> None:
    ids = Counter(q.id for q in dataset.queries)
    for qid, count in ids.items():
        if count > 1:
            report.errors.append(f"query id {qid!r} is used {count} times")

    seen: dict[str, str] = {}
    for q in dataset.queries:
        key = " ".join(normalize_for_search(q.query).split())
        if key in seen and not q.history:
            report.warnings.append(f"{q.id}: same question as {seen[key]}")
        seen.setdefault(key, q.id)

        bangla = _has_bangla(q.query)
        if q.language == "bn" and not bangla:
            report.errors.append(f"{q.id}: language 'bn' but the query has no Bangla script")
        if q.language in ("en", "banglish") and bangla:
            report.errors.append(f"{q.id}: language {q.language!r} but the query has Bangla script")

        if q.category == "cross_lingual":
            doc_langs = {
                entry.language for rel in q.relevant if (entry := dataset.document(rel.doc))
            }
            query_lang = "bn" if bangla else "en"
            if query_lang in doc_langs:
                report.errors.append(
                    f"{q.id}: cross_lingual, but the query and its document are both {query_lang!r}"
                )


def _check_balance(dataset: RagDataset, report: Report) -> None:
    by_split: dict[str, Counter] = defaultdict(Counter)
    for q in dataset.queries:
        by_split[q.split][q.category] += 1
    report.counts = dict(by_split)
    for category, count in sorted(by_split.get("test", Counter()).items()):
        if count < MIN_PER_CATEGORY:
            report.warnings.append(
                f"test/{category}: {count} queries (aim for {MIN_PER_CATEGORY}+ per category)"
            )
    docs_by_split = Counter(d.split for d in dataset.manifest.documents)
    if docs_by_split["test"] == 0:
        report.errors.append("no test documents")
    unpublishable = [d.name for d in dataset.manifest.documents if not d.publishable]
    if unpublishable:
        report.warnings.append(f"not publishable, exclude when uploading: {', '.join(unpublishable)}")


def validate_dataset(dataset: RagDataset) -> Report:
    report = Report()
    parsed = _parse(dataset, report)
    _check_labels(dataset, parsed, report)
    _check_queries(dataset, report)
    _check_balance(dataset, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a v2 bilingual RAG dataset")
    parser.add_argument("root", help="Dataset folder with manifest.json and queries.jsonl")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    try:
        dataset = load_rag_dataset(args.root)
    except (OSError, ValueError) as exc:
        print(f"ERROR {exc}")
        sys.exit(1)
    report = validate_dataset(dataset)

    print(f"{dataset.manifest.name} v{dataset.manifest.version}: "
          f"{len(dataset.manifest.documents)} documents, {len(dataset.queries)} queries")
    for split, counts in sorted(report.counts.items()):
        summary = ", ".join(f"{cat} {n}" for cat, n in sorted(counts.items()))
        print(f"  {split}: {sum(counts.values())} ({summary})")
    for message in report.errors:
        print(f"ERROR   {message}")
    for message in report.warnings:
        print(f"WARNING {message}")
    print("OK" if report.ok else f"{len(report.errors)} error(s)")
    sys.exit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
