"""Information Retrieval (IR) evaluation metrics.

Provides Recall@K, Reciprocal Rank (RR), Mean Reciprocal Rank (MRR),
Discounted Cumulative Gain (DCG@K), and Normalized Discounted Cumulative Gain (nDCG@K).
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def compute_recall_at_k(
    retrieved: Sequence[str],
    relevant: set[str] | Sequence[str],
    k: int = 5,
) -> float:
    """Compute Recall@K.

    Recall@K measures what proportion of all known relevant items
    were successfully retrieved within the top K results.

    Args:
        retrieved: Ordered list of retrieved passage/chunk IDs.
        relevant: Set or sequence of ground-truth relevant passage/chunk IDs.
        k: Cut-off rank (default: 5).

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 if relevant is empty or k <= 0.
    """
    if k <= 0 or not retrieved or not relevant:
        return 0.0

    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0

    # Avoid duplicate counting in retrieved top-k
    retrieved_top_k_unique = set(retrieved[:k])
    hits = len(retrieved_top_k_unique & relevant_set)
    return hits / len(relevant_set)


def compute_reciprocal_rank(
    retrieved: Sequence[str],
    relevant: set[str] | Sequence[str],
    k: int | None = None,
) -> float:
    """Compute Reciprocal Rank (RR).

    RR is 1 / rank of the FIRST relevant item found. If the first relevant
    item is at rank 1, RR is 1.0; at rank 2, RR is 0.5; etc.

    Args:
        retrieved: Ordered list of retrieved passage/chunk IDs.
        relevant: Set or sequence of ground-truth relevant passage/chunk IDs.
        k: Optional cut-off rank. If provided, searches only within retrieved[:k].

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 if no relevant item is found.
    """
    if not retrieved or not relevant:
        return 0.0

    if k is not None and k <= 0:
        return 0.0

    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0

    candidates = retrieved[:k] if k is not None else retrieved
    for rank, item in enumerate(candidates, start=1):
        if item in relevant_set:
            return 1.0 / rank

    return 0.0


def compute_mrr(
    eval_results: Sequence[tuple[Sequence[str], set[str] | Sequence[str]]],
    k: int | None = None,
) -> float:
    """Compute Mean Reciprocal Rank (MRR) across multiple queries.

    MRR is the arithmetic mean of Reciprocal Ranks over all evaluated queries.

    Args:
        eval_results: Sequence of (retrieved_ids, relevant_ids) tuples for each query.
        k: Optional cut-off rank applied to each query.

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 if eval_results is empty.
    """
    if not eval_results:
        return 0.0

    total_rr = sum(compute_reciprocal_rank(ret, rel, k=k) for ret, rel in eval_results)
    return total_rr / len(eval_results)


def compute_dcg_at_k(
    retrieved: Sequence[str],
    relevance_grades: dict[str, int],
    k: int = 5,
) -> float:
    """Compute Discounted Cumulative Gain at rank K (DCG@K).

    Uses the standard graded relevance formulation:
        DCG@K = sum_{i=1}^{min(k, len(retrieved))} (2^{rel_i} - 1) / log2(i + 1)

    Args:
        retrieved: Ordered list of retrieved passage/chunk IDs.
        relevance_grades: Mapping from passage/chunk ID to integer grade (e.g., 0 to 3).
        k: Cut-off rank (default: 5).

    Returns:
        Non-negative float DCG score.
    """
    if k <= 0 or not retrieved or not relevance_grades:
        return 0.0

    dcg = 0.0
    for rank, item in enumerate(retrieved[:k], start=1):
        rel = relevance_grades.get(item, 0)
        if rel > 0:
            gain = (2.0**rel - 1.0) / math.log2(rank + 1)
            dcg += gain

    return dcg


def compute_ndcg_at_k(
    retrieved: Sequence[str],
    relevance_grades: dict[str, int],
    k: int = 5,
) -> float:
    """Compute Normalized Discounted Cumulative Gain at rank K (nDCG@K).

    nDCG@K = DCG@K / IDCG@K, where IDCG@K is the Ideal DCG achieved by
    sorting all known positive grades in descending order.

    Args:
        retrieved: Ordered list of retrieved passage/chunk IDs.
        relevance_grades: Mapping from passage/chunk ID to integer grade.
        k: Cut-off rank (default: 5).

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 if IDCG@K is 0 (no positive grades).
    """
    if k <= 0 or not relevance_grades:
        return 0.0

    # Sort all positive ground-truth grades descending to form the ideal ranking
    positive_grades = sorted([g for g in relevance_grades.values() if g > 0], reverse=True)
    if not positive_grades:
        return 0.0

    idcg = sum(
        (2.0**grade - 1.0) / math.log2(rank + 1)
        for rank, grade in enumerate(positive_grades[:k], start=1)
    )
    if idcg == 0.0:
        return 0.0

    dcg = compute_dcg_at_k(retrieved, relevance_grades, k=k)
    return dcg / idcg
