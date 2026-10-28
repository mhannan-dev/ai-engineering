"""Tests for Information Retrieval (IR) evaluation metrics."""

import math

import pytest

from knowledge_worker.evaluation.metrics import (
    compute_dcg_at_k,
    compute_mrr,
    compute_ndcg_at_k,
    compute_recall_at_k,
    compute_reciprocal_rank,
)


class TestRecallAtK:
    def test_single_relevant_hit_in_top_k(self):
        retrieved = ["chunk_a", "chunk_b", "chunk_c"]
        relevant = {"chunk_a"}
        assert compute_recall_at_k(retrieved, relevant, k=1) == 1.0
        assert compute_recall_at_k(retrieved, relevant, k=3) == 1.0

    def test_single_relevant_miss_due_to_k_cutoff(self):
        retrieved = ["chunk_a", "chunk_b", "chunk_c"]
        relevant = {"chunk_b"}
        # chunk_b is at rank 2, so with k=1 it should be a miss
        assert compute_recall_at_k(retrieved, relevant, k=1) == 0.0
        # with k=2 it is captured
        assert compute_recall_at_k(retrieved, relevant, k=2) == 1.0

    def test_multiple_relevant_partial_recall(self):
        retrieved = ["c1", "miss1", "c2", "miss2", "c3"]
        relevant = {"c1", "c2", "c3"}
        # At k=1: only c1 -> 1/3
        assert compute_recall_at_k(retrieved, relevant, k=1) == pytest.approx(1 / 3)
        # At k=3: c1 and c2 -> 2/3
        assert compute_recall_at_k(retrieved, relevant, k=3) == pytest.approx(2 / 3)
        # At k=5: c1, c2, c3 -> 3/3 = 1.0
        assert compute_recall_at_k(retrieved, relevant, k=5) == 1.0

    def test_relevant_with_duplicates_handled_correctly(self):
        retrieved = ["c1", "c2"]
        # Sequence of relevant with duplicate IDs
        relevant = ["c1", "c1"]
        # Should treat unique target count as 1, so retrieving c1 gives 1/1 = 1.0
        assert compute_recall_at_k(retrieved, relevant, k=5) == 1.0

    def test_retrieved_duplicates_do_not_inflate_recall(self):
        retrieved = ["c1", "c1", "miss"]
        relevant = {"c1", "c2"}
        # Only c1 is found once, c2 missing -> 1/2 = 0.5, not 2/2
        assert compute_recall_at_k(retrieved, relevant, k=5) == pytest.approx(0.5)

    def test_empty_inputs(self):
        assert compute_recall_at_k([], {"c1"}, k=5) == 0.0
        assert compute_recall_at_k(["c1"], set(), k=5) == 0.0
        assert compute_recall_at_k(["c1"], {"c1"}, k=0) == 0.0
        assert compute_recall_at_k(["c1"], {"c1"}, k=-1) == 0.0


class TestReciprocalRank:
    def test_rank_one_hit(self):
        retrieved = ["c1", "c2", "c3"]
        assert compute_reciprocal_rank(retrieved, {"c1"}) == 1.0

    def test_rank_two_hit(self):
        retrieved = ["c1", "c2", "c3"]
        assert compute_reciprocal_rank(retrieved, {"c2"}) == 0.5

    def test_rank_three_hit(self):
        retrieved = ["c1", "c2", "c3"]
        assert compute_reciprocal_rank(retrieved, {"c3"}) == pytest.approx(1 / 3)

    def test_first_relevant_item_used_when_multiple_present(self):
        retrieved = ["miss", "hit_a", "hit_b"]
        # Both hit_a and hit_b are relevant, but hit_a is at rank 2
        assert compute_reciprocal_rank(retrieved, {"hit_a", "hit_b"}) == 0.5

    def test_k_cutoff_ignores_later_hits(self):
        retrieved = ["miss1", "miss2", "hit"]
        # Hit is at rank 3, so with k=2 it's treated as not found
        assert compute_reciprocal_rank(retrieved, {"hit"}, k=2) == 0.0
        assert compute_reciprocal_rank(retrieved, {"hit"}, k=3) == pytest.approx(1 / 3)

    def test_not_found_returns_zero(self):
        assert compute_reciprocal_rank(["c1", "c2"], {"other"}) == 0.0
        assert compute_reciprocal_rank([], {"c1"}) == 0.0
        assert compute_reciprocal_rank(["c1"], set()) == 0.0


class TestMRR:
    def test_mrr_average_across_queries(self):
        # Query 1: hit at rank 1 -> RR = 1.0
        # Query 2: hit at rank 2 -> RR = 0.5
        # Query 3: no hit -> RR = 0.0
        eval_results = [
            (["hit1", "c2"], {"hit1"}),
            (["miss", "hit2"], {"hit2"}),
            (["miss1", "miss2"], {"target"}),
        ]
        # (1.0 + 0.5 + 0.0) / 3 = 0.5
        assert compute_mrr(eval_results) == pytest.approx(0.5)

    def test_mrr_empty_results(self):
        assert compute_mrr([]) == 0.0


class TestDCGAndNDCG:
    def test_dcg_calculation_hand_computed(self):
        # Grades: d1=3, d2=2, d3=1
        grades = {"d1": 3, "d2": 2, "d3": 1}
        retrieved = ["d1", "d2", "d3"]
        # Rank 1: (2^3 - 1) / log2(2) = 7 / 1 = 7.0
        # Rank 2: (2^2 - 1) / log2(3) = 3 / 1.5849625... ~= 1.892789
        # Rank 3: (2^1 - 1) / log2(4) = 1 / 2 = 0.5
        expected_dcg = 7.0 + (3.0 / math.log2(3)) + 0.5
        assert compute_dcg_at_k(retrieved, grades, k=3) == pytest.approx(expected_dcg)

    def test_dcg_with_unrated_items_treated_as_zero(self):
        grades = {"d1": 2}
        retrieved = ["unrated", "d1"]
        # Rank 1: rel=0 -> (2^0 - 1)/1 = 0
        # Rank 2: rel=2 -> (2^2 - 1)/log2(3) = 3 / log2(3)
        expected_dcg = 3.0 / math.log2(3)
        assert compute_dcg_at_k(retrieved, grades, k=2) == pytest.approx(expected_dcg)

    def test_ndcg_perfect_ranking_is_one(self):
        grades = {"d1": 3, "d2": 2, "d3": 1}
        # In ideal order:
        retrieved = ["d1", "d2", "d3"]
        assert compute_ndcg_at_k(retrieved, grades, k=3) == pytest.approx(1.0)
        assert compute_ndcg_at_k(retrieved, grades, k=5) == pytest.approx(1.0)

    def test_ndcg_suboptimal_ranking(self):
        grades = {"d1": 3, "d2": 2, "d3": 1}
        # Reverse order: d3, d2, d1
        retrieved = ["d3", "d2", "d1"]
        # DCG@3:
        # Rank 1: (2^1 - 1)/1 = 1.0
        # Rank 2: (2^2 - 1)/log2(3) = 3 / log2(3)
        # Rank 3: (2^3 - 1)/log2(4) = 7 / 2 = 3.5
        dcg = 1.0 + (3.0 / math.log2(3)) + 3.5
        # IDCG@3:
        idcg = 7.0 + (3.0 / math.log2(3)) + 0.5
        expected_ndcg = dcg / idcg
        assert compute_ndcg_at_k(retrieved, grades, k=3) == pytest.approx(expected_ndcg)

    def test_ndcg_no_relevant_items_returns_zero(self):
        grades = {"d1": 3}
        retrieved = ["other1", "other2"]
        assert compute_ndcg_at_k(retrieved, grades, k=5) == 0.0

    def test_ndcg_empty_or_zero_grades_returns_zero(self):
        assert compute_ndcg_at_k(["d1"], {}, k=5) == 0.0
        assert compute_ndcg_at_k(["d1"], {"d1": 0}, k=5) == 0.0
        assert compute_ndcg_at_k([], {"d1": 3}, k=5) == 0.0
