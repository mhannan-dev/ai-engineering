"""Reciprocal Rank Fusion (RRF).

Dense (cosine, roughly 0..1) and BM25 (0..unbounded) scores live on different scales, so
adding them directly lets one retriever drown out the other. RRF ignores the raw scores and
only uses each item's *rank* in every list:

    score(d) = sum over lists L containing d of  1 / (k + rank_L(d))      rank is 1-based

Reference: Cormack, Clarke & Buettcher, "Reciprocal Rank Fusion outperforms Condorcet and
individual Rank Learning Methods" (SIGIR 2009). k = 60 is the value from the paper and the
default in Elasticsearch, OpenSearch and Qdrant.
"""

from collections import defaultdict
from collections.abc import Sequence

DEFAULT_RRF_K = 60


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[str]],
    k: int = DEFAULT_RRF_K,
    limit: int | None = None,
) -> list[tuple[str, float]]:
    """Fuse several best-first ranked lists of ids into one ranking.

    Args:
        ranked_lists: Each inner sequence is one retriever's result ids, best first
            (e.g. dense chunk ids, BM25 chunk ids). Any of them may be empty.
        k: Smoothing constant. Must be > 0. Larger k flattens the gap between rank 1 and
            rank 10; smaller k rewards top positions more strongly.
        limit: Return at most this many items. `None` returns all. Must be >= 0.

    Returns:
        `[(id, rrf_score), ...]` sorted by score, highest first.

    Rules:
        - Rank is 1-based: the first item of a list contributes `1 / (k + 1)`.
        - An id appearing in several lists gets the sum of its contributions.
        - If an id repeats inside the *same* list, only its first (best) position counts.
        - Ties on score are broken by id in ascending order, so output is deterministic.
        - Input sequences must not be modified.

    Raises:
        ValueError: if `k <= 0` or `limit < 0`.

    Example:
        >>> reciprocal_rank_fusion([["a", "b"], ["b", "c"]], k=60)
        [('b', 0.0325...), ('a', 0.0163...), ('c', 0.0161...)]
    """
    if k <= 0:
        raise ValueError(f"k must be > 0, got {k}")
    if limit is not None and limit < 0:
        raise ValueError(f"limit must be >= 0, got {limit}")

    scores: defaultdict[str, float] = defaultdict(float)
    for ranked in ranked_lists:
        seen: set[str] = set()
        for rank, doc_id in enumerate(ranked, start=1):
            if doc_id in seen:  # only the best position inside one list counts
                continue
            seen.add(doc_id)
            scores[doc_id] += 1.0 / (k + rank)

    # Highest score first; equal scores fall back to id so the order is reproducible.
    fused = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return fused if limit is None else fused[:limit]
