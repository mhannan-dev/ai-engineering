"""Unit tests for citation extraction and grounding validator."""

from knowledge_worker.generation.validator import CitationValidator
from knowledge_worker.retrieval.models import RerankedChunk
from knowledge_worker.schemas.generation import Citation


def test_extract_citations_various_formats():
    validator = CitationValidator()

    text = (
        "Employees get 20 days of annual leave [leave_policy.pdf, Page 2]. "
        "For travel, per diem is standard [handbook.md, Travel Allowance]. "
        "Check overall benefits [benefits.docx]. "
        "And multi-source rules [handbook.md, Page 5; appendix.pdf, Page 10]."
    )

    citations = validator.extract_citations(text)
    filenames = [c.document_filename for c in citations]

    assert "leave_policy.pdf" in filenames
    assert "handbook.md" in filenames
    assert "benefits.docx" in filenames
    assert "appendix.pdf" in filenames

    # Verify parsed page and heading
    leave_cit = next(c for c in citations if c.document_filename == "leave_policy.pdf")
    assert leave_cit.page == 2

    travel_cit = next(c for c in citations if c.document_filename == "handbook.md" and c.heading)
    assert travel_cit.heading == "Travel Allowance"

    appendix_cit = next(c for c in citations if c.document_filename == "appendix.pdf")
    assert appendix_cit.page == 10


def test_validator_grounded_citation():
    validator = CitationValidator()

    retrieved = [
        RerankedChunk(
            chunk_id="c1",
            document_id="d1",
            document_filename="handbook.pdf",
            page=3,
            heading="Section 1",
            text="Annual leave is 20 days per year.",
            score=0.9,
            fused_rank=1,
            rerank_rank=1,
        )
    ]

    answer = "Employees receive 20 days of annual leave [handbook.pdf, Page 3]."
    result = validator.validate(answer=answer, retrieved_chunks=retrieved)

    assert result.is_valid is True
    assert len(result.valid_citations) == 1
    assert result.valid_citations[0].document_filename == "handbook.pdf"
    assert result.valid_citations[0].page == 3
    assert result.valid_citations[0].chunk_id == "c1"
    assert len(result.hallucinated_citations) == 0
    assert len(result.unmatched_pages) == 0


def test_validator_hallucinated_document():
    validator = CitationValidator()

    retrieved = [
        RerankedChunk(
            chunk_id="c1",
            document_id="d1",
            document_filename="handbook.pdf",
            page=1,
            heading=None,
            text="Official office handbook text.",
            score=0.85,
            fused_rank=1,
            rerank_rank=1,
        )
    ]

    # Cites 'confidential_memo.pdf' which was never retrieved!
    answer = "Salary increase is 15% [confidential_memo.pdf, Page 1]."
    result = validator.validate(answer=answer, retrieved_chunks=retrieved)

    assert result.is_valid is False
    assert len(result.hallucinated_citations) == 1
    assert result.hallucinated_citations[0].document_filename == "confidential_memo.pdf"
    assert any("Hallucinated source" in w for w in result.warnings)


def test_validator_unmatched_page():
    validator = CitationValidator()

    retrieved = [
        RerankedChunk(
            chunk_id="c1",
            document_id="d1",
            document_filename="handbook.pdf",
            page=2,
            heading=None,
            text="Handbook content on page 2.",
            score=0.88,
            fused_rank=1,
            rerank_rank=1,
        )
    ]

    # Document matches, but cites page 99!
    answer = "Remote work rules are flexible [handbook.pdf, Page 99]."
    result = validator.validate(answer=answer, retrieved_chunks=retrieved)

    assert result.is_valid is False
    assert len(result.unmatched_pages) == 1
    assert result.unmatched_pages[0].page == 99
    assert any("Page mismatch" in w for w in result.warnings)


def test_validator_structured_citation_support():
    validator = CitationValidator()

    retrieved = [
        RerankedChunk(
            chunk_id="c1",
            document_id="d1",
            document_filename="rules.md",
            page=None,
            heading="Leaves",
            text="Leaves must be submitted 3 days in advance.",
            score=0.8,
            fused_rank=1,
            rerank_rank=1,
        )
    ]

    structured = [
        Citation(document_filename="rules.md", heading="Leaves", quoted_text="3 days in advance")
    ]
    answer = "Submit leave early [rules.md, Leaves]."

    result = validator.validate(
        answer=answer, retrieved_chunks=retrieved, structured_citations=structured
    )

    assert result.is_valid is True
    assert len(result.valid_citations) == 1
    assert result.valid_citations[0].document_filename == "rules.md"
