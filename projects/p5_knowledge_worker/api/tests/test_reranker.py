"""Tests for Phase 3 Cross-Encoder Reranking and Abstention Thresholding."""

import pytest

from knowledge_worker.retrieval.reranker import (
    RerankResult,
    rerank_candidates,
)
from knowledge_worker.retrieval.retriever import RetrievedChunk


class MockReranker:
    def __init__(self, score_map: dict[str, float]):
        self.score_map = score_map

    def rerank(self, query: str, passages: list[str]) -> list[float]:
        return [self.score_map.get(p, 0.0) for p in passages]


def make_candidate(cid: str, text: str, score: float = 0.02) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=cid,
        document_id="doc-1",
        document_filename="handbook.md",
        page=1,
        heading="Policy",
        text=text,
        score=score,
    )


class TestReranker:
    def test_rerank_sorts_by_cross_encoder_score_descending(self):
        # Candidate 2 was #2 in fused ranking, but cross-encoder scores it highest
        c1 = make_candidate("cid-1", "Passage about vacation")
        c2 = make_candidate("cid-2", "Passage about annual leave balance")
        c3 = make_candidate("cid-3", "Passage about sick leaves")

        reranker = MockReranker({
            "Passage about vacation": 0.40,
            "Passage about annual leave balance": 0.95,
            "Passage about sick leaves": 0.15,
        })

        result = rerank_candidates("annual leave", [c1, c2, c3], reranker, threshold=0.25)

        assert isinstance(result, RerankResult)
        assert result.is_abstention is False
        assert len(result.chunks) == 3

        # First hit should now be c2
        assert result.chunks[0].chunk_id == "cid-2"
        assert result.chunks[0].score == pytest.approx(0.95)
        assert result.chunks[0].rerank_rank == 1
        assert result.chunks[0].fused_rank == 2  # original rank preserved

        # Second hit is c1
        assert result.chunks[1].chunk_id == "cid-1"
        assert result.chunks[1].rerank_rank == 2
        assert result.chunks[1].fused_rank == 1

        # Third hit is c3
        assert result.chunks[2].chunk_id == "cid-3"
        assert result.chunks[2].rerank_rank == 3
        assert result.chunks[2].fused_rank == 3

    def test_abstains_when_top_score_below_threshold(self):
        # Query about Mars agriculture when docs are HR policies
        c1 = make_candidate("cid-1", "Leave policy details")
        c2 = make_candidate("cid-2", "Travel reimbursement rules")

        reranker = MockReranker({
            "Leave policy details": 0.12,
            "Travel reimbursement rules": 0.08,
        })

        result = rerank_candidates(
            "How to grow potatoes on Mars?",
            [c1, c2],
            reranker,
            threshold=0.25,
        )

        assert result.is_abstention is True
        assert result.threshold == 0.25
        assert len(result.chunks) == 2
        assert result.chunks[0].score < 0.25

    def test_empty_candidates_returns_abstention(self):
        reranker = MockReranker({})
        result = rerank_candidates("anything", [], reranker, threshold=0.25)

        assert result.is_abstention is True
        assert result.chunks == []

    def test_ties_broken_by_chunk_id_ascending(self):
        c_beta = make_candidate("b-chunk", "Same text")
        c_alpha = make_candidate("a-chunk", "Same text")

        reranker = MockReranker({"Same text": 0.80})

        result = rerank_candidates("query", [c_beta, c_alpha], reranker, threshold=0.25)

        assert [c.chunk_id for c in result.chunks] == ["a-chunk", "b-chunk"]

    def test_limit_truncates_after_reranking(self):
        c1 = make_candidate("cid-1", "Low relevance")
        c2 = make_candidate("cid-2", "Medium relevance")
        c3 = make_candidate("cid-3", "Highest relevance")

        reranker = MockReranker({
            "Low relevance": 0.30,
            "Medium relevance": 0.60,
            "Highest relevance": 0.90,
        })

        result = rerank_candidates("query", [c1, c2, c3], reranker, limit=2)

        assert len(result.chunks) == 2
        assert result.chunks[0].chunk_id == "cid-3"
        assert result.chunks[1].chunk_id == "cid-2"
