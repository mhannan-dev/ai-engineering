import pytest

from knowledge_worker.retrieval.fusion import DEFAULT_RRF_K, reciprocal_rank_fusion


def ids(fused: list[tuple[str, float]]) -> list[str]:
    return [doc_id for doc_id, _ in fused]


class TestScoring:
    def test_default_k_is_60(self):
        assert DEFAULT_RRF_K == 60

    def test_single_list_keeps_order_with_1_based_ranks(self):
        fused = reciprocal_rank_fusion([["a", "b", "c"]])
        assert ids(fused) == ["a", "b", "c"]
        assert fused[0][1] == pytest.approx(1 / 61)
        assert fused[1][1] == pytest.approx(1 / 62)
        assert fused[2][1] == pytest.approx(1 / 63)

    def test_id_in_both_lists_gets_summed_score(self):
        fused = dict(reciprocal_rank_fusion([["a", "b"], ["b", "c"]]))
        assert fused["b"] == pytest.approx(1 / 62 + 1 / 61)
        assert fused["a"] == pytest.approx(1 / 61)
        assert fused["c"] == pytest.approx(1 / 62)

    def test_consensus_beats_a_single_top_hit(self):
        # "x" is #1 in dense only; "y" is #3 in both. Agreement should win.
        dense = ["x", "d2", "y"]
        bm25 = ["s1", "s2", "y"]
        fused = reciprocal_rank_fusion([dense, bm25])
        assert ids(fused)[0] == "y"
        assert dict(fused)["y"] == pytest.approx(2 / 63)

    def test_custom_k_changes_weights(self):
        fused = reciprocal_rank_fusion([["a", "b"]], k=1)
        assert fused == [("a", pytest.approx(1 / 2)), ("b", pytest.approx(1 / 3))]

    def test_three_lists(self):
        fused = reciprocal_rank_fusion([["a"], ["a"], ["b"]])
        assert ids(fused) == ["a", "b"]
        assert dict(fused)["a"] == pytest.approx(2 / 61)


class TestEdgeCases:
    @pytest.mark.parametrize("lists", [[], [[]], [[], []]])
    def test_no_results_returns_empty(self, lists):
        assert reciprocal_rank_fusion(lists) == []

    def test_one_empty_list_is_ignored(self):
        assert reciprocal_rank_fusion([["a"], []]) == [("a", pytest.approx(1 / 61))]

    def test_duplicate_in_same_list_counts_once_at_best_rank(self):
        fused = dict(reciprocal_rank_fusion([["a", "b", "a"]]))
        assert fused["a"] == pytest.approx(1 / 61)
        assert fused["b"] == pytest.approx(1 / 62)

    def test_ties_are_broken_by_id_ascending(self):
        # Both get 1/61 + 1/62 -> identical scores.
        assert ids(reciprocal_rank_fusion([["b", "a"], ["a", "b"]])) == ["a", "b"]
        assert ids(reciprocal_rank_fusion([["z"], ["y"]])) == ["y", "z"]

    def test_unicode_and_uuid_ids(self):
        uid = "00000000-0000-0000-0000-00000000000a"
        fused = reciprocal_rank_fusion([[uid, "ছুটি"], ["ছুটি"]])
        assert ids(fused) == ["ছুটি", uid]

    def test_does_not_mutate_input(self):
        dense, bm25 = ["a", "b"], ["b", "c"]
        reciprocal_rank_fusion([dense, bm25])
        assert dense == ["a", "b"] and bm25 == ["b", "c"]

    def test_accepts_tuples(self):
        assert ids(reciprocal_rank_fusion((("a", "b"), ("b",)))) == ["b", "a"]


class TestLimit:
    def test_limit_truncates_after_fusion(self):
        # "c" is last in each list but first after fusion; limit must apply to the fused order.
        fused = reciprocal_rank_fusion([["a", "c"], ["b", "c"]], limit=1)
        assert ids(fused) == ["c"]

    def test_limit_none_returns_all(self):
        assert len(reciprocal_rank_fusion([["a", "b", "c"]], limit=None)) == 3

    def test_limit_larger_than_results(self):
        assert len(reciprocal_rank_fusion([["a", "b"]], limit=10)) == 2

    def test_limit_zero_returns_empty(self):
        assert reciprocal_rank_fusion([["a", "b"]], limit=0) == []


class TestValidation:
    @pytest.mark.parametrize("k", [0, -1, -60])
    def test_non_positive_k_raises(self, k):
        with pytest.raises(ValueError):
            reciprocal_rank_fusion([["a"]], k=k)

    def test_negative_limit_raises(self):
        with pytest.raises(ValueError):
            reciprocal_rank_fusion([["a"]], limit=-1)
