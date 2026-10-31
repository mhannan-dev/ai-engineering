"""v2 dataset schema, loader and validator."""

import json
from pathlib import Path

import fitz
import pytest
from pydantic import ValidationError

from knowledge_worker.evaluation.rag_dataset import DatasetQuery, load_rag_dataset
from knowledge_worker.evaluation.validate import validate_dataset

REPO_DATASET = Path(__file__).resolve().parents[2] / "datasets" / "bilingual_rag_eval"


def query(**overrides) -> dict:
    base = {
        "id": "q1",
        "query": "How many days of annual leave?",
        "language": "en",
        "category": "english",
        "answerable": True,
        "relevant": [{"doc": "policy.md", "section": "Leave", "grade": 3}],
        "answer": "20 days",
        "split": "test",
    }
    return {**base, **overrides}


class TestSchema:
    def test_valid_query(self):
        assert DatasetQuery.model_validate(query()).relevant[0].section == "Leave"

    @pytest.mark.parametrize(
        "overrides",
        [
            {"category": "unanswerable"},  # unanswerable but answerable=true
            {"category": "english", "answerable": False, "relevant": [], "answer": None},
            {"relevant": []},
            {"answer": None},
            {"category": "follow_up"},  # follow_up without history
            {"history": [["q", "a"]]},  # history on a non-follow-up
            {"id": "Has Spaces"},
            {"split": "dev"},
        ],
    )
    def test_inconsistent_queries_are_rejected(self, overrides):
        with pytest.raises(ValidationError):
            DatasetQuery.model_validate(query(**overrides))

    def test_follow_up_with_history(self):
        q = DatasetQuery.model_validate(
            query(category="follow_up", query="And sick leave?", history=[["Annual leave?", "20 days"]])
        )
        assert q.history == [("Annual leave?", "20 days")]

    def test_section_is_normalized_like_stored_headings(self):
        q = DatasetQuery.model_validate(
            query(relevant=[{"doc": "a.md", "section": "সময়", "grade": 3}])
        )
        assert "য়" not in q.relevant[0].section  # NFC decomposes precomposed য়


def write_dataset(root: Path, documents: list[dict], queries: list[dict]) -> Path:
    (root / "manifest.json").write_text(
        json.dumps({"name": "t", "version": "0", "documents": documents}), encoding="utf-8"
    )
    (root / "queries.jsonl").write_text(
        "\n".join(json.dumps(q, ensure_ascii=False) for q in queries), encoding="utf-8"
    )
    return root


def doc(name: str, split: str = "test", language: str = "en", **extra) -> dict:
    return {
        "name": name, "path": name, "split": split, "language": language,
        "license": "CC-BY-4.0", "source": "synthetic", "publishable": True, **extra,
    }


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "policy.md").write_text("# Leave\n\nEmployees get 20 days.\n", encoding="utf-8")
    (tmp_path / "train.md").write_text("# Travel\n\nDaily allowance is 1500.\n", encoding="utf-8")
    (tmp_path / "plain.txt").write_text("No headings here at all.\n", encoding="utf-8")
    (tmp_path / "bn.md").write_text("# ছুটি\n\nবছরে ২০ দিন ছুটি।\n", encoding="utf-8")
    pdf = fitz.open()
    for text in ("Page one text.", "Page two text."):
        pdf.new_page().insert_text((72, 72), text)
    pdf.save(tmp_path / "manual.pdf")
    return tmp_path


DOCS = [
    doc("policy.md"), doc("train.md", split="train"), doc("plain.txt"),
    doc("bn.md", language="bn"), doc("manual.pdf"),
]


def errors_for(root: Path, queries: list[dict], documents: list[dict] = DOCS) -> list[str]:
    return validate_dataset(load_rag_dataset(write_dataset(root, documents, queries))).errors


class TestValidator:
    def test_clean_dataset(self, root):
        assert errors_for(root, [query()]) == []

    def test_unknown_section(self, root):
        errors = errors_for(root, [query(relevant=[{"doc": "policy.md", "section": "Sick", "grade": 3}])])
        assert any("section 'Sick' not found" in e for e in errors)

    def test_document_level_label_only_without_headings(self, root):
        assert errors_for(root, [query(relevant=[{"doc": "plain.txt", "section": None, "grade": 3}])]) == []
        errors = errors_for(root, [query(relevant=[{"doc": "policy.md", "section": None, "grade": 3}])])
        assert any("needs an exact section" in e for e in errors)

    def test_pdf_page_must_exist(self, root):
        ok = query(relevant=[{"doc": "manual.pdf", "section": None, "page": 2, "grade": 3}])
        assert errors_for(root, [ok]) == []
        bad = query(relevant=[{"doc": "manual.pdf", "section": None, "page": 9, "grade": 3}])
        assert any("page 9 not found" in e for e in errors_for(root, [bad]))

    def test_leakage_between_splits(self, root):
        leak = query(relevant=[{"doc": "train.md", "section": "Travel", "grade": 3}])
        assert any("which is in train" in e for e in errors_for(root, [leak]))

    def test_unknown_and_missing_documents(self, root):
        unknown = query(relevant=[{"doc": "nope.md", "section": "X", "grade": 3}])
        assert any("not in the manifest" in e for e in errors_for(root, [unknown]))
        missing = errors_for(root, [query()], documents=[*DOCS, doc("ghost.md")])
        assert any("file not found" in e for e in missing)

    def test_language_must_match_script(self, root):
        assert any("no Bangla script" in e for e in errors_for(root, [query(language="bn")]))
        banglish = query(language="banglish", category="banglish", query="ছুটি কত দিন?")
        assert any("has Bangla script" in e for e in errors_for(root, [banglish]))

    def test_cross_lingual_needs_different_languages(self, root):
        same = query(category="cross_lingual", relevant=[{"doc": "policy.md", "section": "Leave", "grade": 3}])
        assert any("both 'en'" in e for e in errors_for(root, [same]))
        good = query(category="cross_lingual", relevant=[{"doc": "bn.md", "section": "ছুটি", "grade": 3}])
        assert errors_for(root, [good]) == []

    def test_duplicate_ids_and_questions(self, root):
        dataset = load_rag_dataset(write_dataset(root, DOCS, [query(), query(), query(id="q2", query="how many days of ANNUAL leave?")]))
        report = validate_dataset(dataset)
        assert any("used 2 times" in e for e in report.errors)
        assert any("same question as q1" in w for w in report.warnings)

    def test_bad_line_is_named(self, root):
        (root / "manifest.json").write_text(json.dumps({"name": "t", "version": "0", "documents": DOCS}))
        (root / "queries.jsonl").write_text(json.dumps(query()) + "\n{not json\n", encoding="utf-8")
        with pytest.raises(ValueError, match="line 2"):
            load_rag_dataset(root)


def test_committed_dataset_is_valid():
    report = validate_dataset(load_rag_dataset(REPO_DATASET))
    assert report.errors == []
