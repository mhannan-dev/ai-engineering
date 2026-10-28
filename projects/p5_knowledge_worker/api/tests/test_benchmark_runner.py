"""Tests for the retrieval benchmark and ablation runner."""

from unittest.mock import MagicMock

import pytest

from knowledge_worker.evaluation.dataset import EvalQuery, EvalRelevanceGrade
from knowledge_worker.evaluation.runner import (
    evaluate_hits,
    grade_chunk,
    run_retrieval_benchmark,
)
from knowledge_worker.retrieval.models import (
    RerankedChunk,
    RetrievedChunk,
    SearchDebugResult,
)


@pytest.fixture
def sample_query() -> EvalQuery:
    return EvalQuery(
        id="test_q1",
        query="What is the max upload size?",
        category="english",
        is_answerable=True,
        expected_doc="retrieval_operations_handbook.md",
        expected_heading="5. File size and duplicate handling",
        expected_fact="Max 25 MiB",
        relevance_grades=[
            EvalRelevanceGrade(
                document_filename="retrieval_operations_handbook.md",
                heading="5. File size and duplicate handling",
                grade=3,
            ),
            EvalRelevanceGrade(
                document_filename="retrieval_operations_handbook.md",
                heading="4. Accepted file formats",
                grade=1,
            ),
        ],
    )


def test_grade_chunk_matches(sample_query):
    # Grade 3 match
    c_exact = RetrievedChunk(
        chunk_id="c1",
        document_id="d1",
        document_filename="retrieval_operations_handbook.md",
        page=1,
        heading="5. File size and duplicate handling",
        text="25 MiB max upload size",
        score=0.95,
    )
    assert grade_chunk(c_exact, sample_query) == 3

    # Grade 1 match
    c_partial = RetrievedChunk(
        chunk_id="c2",
        document_id="d1",
        document_filename="retrieval_operations_handbook.md",
        page=1,
        heading="4. Accepted file formats",
        text="Accepted formats",
        score=0.5,
    )
    assert grade_chunk(c_partial, sample_query) == 1

    # Completely irrelevant chunk
    c_irrelevant = RetrievedChunk(
        chunk_id="c3",
        document_id="d2",
        document_filename="bangla_community_service_handbook.md",
        page=1,
        heading="২. খোলা ও বন্ধের সময়",
        text="অন্য নথি",
        score=0.1,
    )
    assert grade_chunk(c_irrelevant, sample_query) == 0


def test_evaluate_hits(sample_query):
    hit_relevant = RetrievedChunk(
        chunk_id="c1",
        document_id="d1",
        document_filename="retrieval_operations_handbook.md",
        page=1,
        heading="5. File size and duplicate handling",
        text="25 MiB",
        score=0.9,
    )
    hit_miss = RetrievedChunk(
        chunk_id="c_other",
        document_id="d2",
        document_filename="other.md",
        page=1,
        heading="Other",
        text="other",
        score=0.1,
    )

    # When relevant hit is at rank 1
    recall, rr, ndcg = evaluate_hits([hit_relevant, hit_miss], sample_query, k=5)
    assert recall == 1.0
    assert rr == 1.0
    assert ndcg == pytest.approx(1.0)

    # When relevant hit is at rank 2
    recall2, rr2, ndcg2 = evaluate_hits([hit_miss, hit_relevant], sample_query, k=5)
    assert recall2 == 1.0
    assert rr2 == 0.5
    assert 0.0 < ndcg2 < 1.0


def test_run_retrieval_benchmark_mocked(sample_query):
    mock_retriever = MagicMock()
    hit_relevant = RetrievedChunk(
        chunk_id="c1",
        document_id="d1",
        document_filename="retrieval_operations_handbook.md",
        page=1,
        heading="5. File size and duplicate handling",
        text="25 MiB",
        score=0.9,
    )
    hit_miss = RetrievedChunk(
        chunk_id="c_other",
        document_id="d2",
        document_filename="other.md",
        page=1,
        heading="Other",
        text="other",
        score=0.1,
    )
    reranked_hit = RerankedChunk(
        chunk_id="c1",
        document_id="d1",
        document_filename="retrieval_operations_handbook.md",
        page=1,
        heading="5. File size and duplicate handling",
        text="25 MiB",
        score=0.98,
        fused_rank=1,
        rerank_rank=1,
    )

    debug_result = SearchDebugResult(
        query=sample_query.query,
        normalized_query=sample_query.query,
        was_banglish=False,
        dense_hits=[hit_relevant],
        sparse_hits=[hit_miss],
        fused_hits=[hit_relevant, hit_miss],
        reranked_hits=[reranked_hit],
    )
    mock_retriever.search_debug.return_value = debug_result

    dataset = [sample_query]
    report = run_retrieval_benchmark(mock_retriever, user_id="user1", dataset=dataset, k=5)

    assert report.total_queries == 1
    assert report.evaluated_answerable == 1
    assert "dense" in report.variants
    assert "sparse" in report.variants
    assert "fused" in report.variants
    assert "reranked" in report.variants

    assert report.variants["dense"].mean_recall_at_5 == 1.0
    assert report.variants["sparse"].mean_recall_at_5 == 0.0
