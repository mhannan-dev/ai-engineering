"""Batch drafting and the review/merge workflow."""

import json
from pathlib import Path

import pytest

from knowledge_worker.evaluation.drafting import (
    DRAFTS_FILE,
    categories_for,
    draft,
    main,
    merge,
    plan,
)
from knowledge_worker.evaluation.question_gen import GeneratedQuestion, GeneratedQuestions
from knowledge_worker.evaluation.rag_dataset import DocumentEntry, load_rag_dataset

EN = DocumentEntry(name="hr.md", path="hr.md", split="test", language="en",
                   license="CC-BY-4.0", source="synthetic", publishable=True)
BN = EN.model_copy(update={"name": "bn.md", "path": "bn.md", "language": "bn"})

HR = """# HR Policy

> Synthetic retrieval-test document. Everything here is fictional.

## 1. Annual leave

Every full-time employee receives 20 working days of paid annual leave per calendar year,
requested in the HR portal under the code LV-ANN.

## 2. Values

We value honesty, kindness and teamwork in everything we do at the company every day.

## 3. Short

Too short.
"""


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def generate_structured(self, messages, response_model, temperature=0.0, max_tokens=1500):
        self.calls += 1
        return GeneratedQuestions(questions=[
            GeneratedQuestion(question="How much paid holiday do staff get yearly?", answer="20 working days"),
            GeneratedQuestion(question="Every full-time employee receives paid annual leave per calendar year?", answer="20"),
        ])


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "hr.md").write_text(HR, encoding="utf-8")
    manifest = {"name": "t", "version": "0", "documents": [EN.model_dump()]}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "queries.jsonl").write_text("", encoding="utf-8")
    return tmp_path


class TestCategories:
    def test_from_section_content(self):
        assert categories_for(EN, "plain words only here") == ["english", "cross_lingual"]
        assert categories_for(EN, "20 days, code LV-ANN") == ["english", "cross_lingual", "numeric", "exact_term"]
        assert categories_for(EN, "Day | Session\nDay 1 | Welcome") == ["english", "cross_lingual", "numeric", "table"]

    def test_bangla_documents_get_banglish(self):
        assert categories_for(BN, "ছুটি ২০ দিন") == ["bangla", "cross_lingual", "banglish", "numeric"]


class TestPlan:
    def test_skips_disclaimers_and_short_sections(self, root):
        jobs = plan(load_rag_dataset(root))
        assert {j.heading for j in jobs} == {"1. Annual leave", "2. Values"}

    def test_drops_the_disclaimer_line_but_keeps_the_rest(self, root):
        # A TXT file is one section, so skipping the whole section would skip the document.
        notice = "Synthetic retrieval-test document. All of it is fictional.\n\n" + (
            "The canteen on the second floor serves lunch from 12:30 to 14:30 on working days. "
        ) * 2
        (root / "notice.txt").write_text(notice, encoding="utf-8")
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        manifest["documents"].append(EN.model_copy(update={"name": "notice.txt", "path": "notice.txt"}).model_dump())
        (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        jobs = [j for j in plan(load_rag_dataset(root), docs=["notice.txt"]) if j.category == "english"]
        assert len(jobs) == 1
        assert jobs[0].text.startswith("The canteen") and "Synthetic" not in jobs[0].text

    def test_filters_by_category(self, root):
        jobs = plan(load_rag_dataset(root), categories=["numeric"])
        assert [(j.heading, j.category) for j in jobs] == [("1. Annual leave", "numeric")]


class TestDraftAndMerge:
    def test_draft_records_carry_review_fields(self, root):
        jobs = plan(load_rag_dataset(root), categories=["english"])
        records = draft(FakeLLM(), jobs, per_section=2)
        assert len(records) == 4
        first = records[0]
        assert first["status"] == "pending"
        assert first["id"] == "test-hr-s02-english-01"
        assert first["passage"].startswith("Every full-time")
        assert [r["keep"] for r in records[:2]] == [True, False]  # the second copies the passage
        assert "copies" in records[1]["reason"]

    def write_drafts(self, root, records):
        (root / DRAFTS_FILE).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")

    def test_merge_appends_only_accepted_and_validates(self, root):
        records = draft(FakeLLM(), plan(load_rag_dataset(root), categories=["english"]), 2)
        records[0]["status"] = "accept"
        records[0]["query"] = "How many days off do I get a year?"  # edited in review
        records[1]["status"] = "reject"
        self.write_drafts(root, records)

        result = merge(root)
        assert (result.added, result.rejected, result.pending, result.errors) == (1, 1, 2, None)
        queries = load_rag_dataset(root).queries
        assert [q.query for q in queries] == ["How many days off do I get a year?"]

        assert merge(root).skipped_duplicates == 1  # merging again adds nothing

    def test_merge_writes_nothing_if_the_result_is_invalid(self, root):
        records = draft(FakeLLM(), plan(load_rag_dataset(root), categories=["english"]), 1)
        records[0]["status"] = "accept"
        records[0]["relevant"][0]["section"] = "No such heading"
        self.write_drafts(root, records)

        result = merge(root)
        assert result.added == 0 and any("not found" in e for e in result.errors)
        assert (root / "queries.jsonl").read_text(encoding="utf-8") == ""


class TestCli:
    def test_dry_run_makes_no_llm_calls(self, root, capsys, monkeypatch):
        monkeypatch.setattr("knowledge_worker.evaluation.drafting._llm", lambda: pytest.fail("LLM used"))
        assert main(["draft", str(root), "--dry-run"]) == 0
        assert "LLM calls" in capsys.readouterr().out
        assert not (root / DRAFTS_FILE).exists()

    def test_draft_refuses_to_overwrite_unmerged_drafts(self, root, monkeypatch):
        llm = FakeLLM()
        monkeypatch.setattr("knowledge_worker.evaluation.drafting._llm", lambda: llm)
        assert main(["draft", str(root), "--categories", "english"]) == 0
        calls = llm.calls
        assert main(["draft", str(root)]) == 1
        assert llm.calls == calls
