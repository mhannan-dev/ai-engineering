"""Benchmark and ablation harness for IR retrieval variants."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from knowledge_worker.evaluation.metrics import (
    compute_ndcg_at_k,
    compute_recall_at_k,
    compute_reciprocal_rank,
)

if TYPE_CHECKING:
    from knowledge_worker.evaluation.dataset import EvalQuery
    from knowledge_worker.retrieval.models import RerankedChunk, RetrievedChunk
    from knowledge_worker.retrieval.retriever import HybridRetriever


class VariantMetrics(BaseModel):
    variant_name: str
    mean_recall_at_5: float = Field(default=0.0)
    mrr: float = Field(default=0.0)
    mean_ndcg_at_5: float = Field(default=0.0)
    avg_latency_ms: float = Field(default=0.0)
    category_recall: dict[str, float] = Field(default_factory=dict)


class BenchmarkReport(BaseModel):
    total_queries: int
    evaluated_answerable: int
    unanswerable_count: int
    variants: dict[str, VariantMetrics]


def grade_chunk(chunk: RetrievedChunk | RerankedChunk, query: EvalQuery) -> int:
    """Determine the relevance grade (0-3) of a retrieved chunk for an EvalQuery.

    Returns:
        3 if it matches a grade-3 ground truth entry (or expected_doc & heading).
        2 or 1 if it matches lower relevance grades.
        0 otherwise.
    """
    if not query.is_answerable:
        return 0

    chunk_doc = (chunk.document_filename or "").strip().lower()
    chunk_heading = (chunk.heading or "").strip().lower()

    matched_grades: list[int] = []
    for grade_item in query.relevance_grades:
        expected_doc = grade_item.document_filename.strip().lower()
        expected_heading = grade_item.heading.strip().lower()

        if chunk_doc == expected_doc or chunk_doc.endswith(expected_doc):
            if expected_heading in chunk_heading or chunk_heading in expected_heading:
                matched_grades.append(grade_item.grade)

    if matched_grades:
        return max(matched_grades)

    if query.expected_doc and query.expected_heading:
        exp_doc = query.expected_doc.strip().lower()
        exp_heading = query.expected_heading.strip().lower()
        if chunk_doc == exp_doc or chunk_doc.endswith(exp_doc):
            if exp_heading in chunk_heading or chunk_heading in exp_heading:
                return 3

    return 0


def evaluate_hits(
    hits: list[RetrievedChunk] | list[RerankedChunk],
    query: EvalQuery,
    k: int = 5,
) -> tuple[float, float, float]:
    """Compute (Recall@K, ReciprocalRank@K, nDCG@K) for a single query's retrieved hits.

    Args:
        hits: List of RetrievedChunk or RerankedChunk from a single retrieval variant.
        query: Ground-truth EvalQuery.
        k: Cut-off rank (default 5).

    Returns:
        Tuple of (recall_at_k, reciprocal_rank, ndcg_at_k).
    """
    if not query.is_answerable:
        # For unanswerable queries, abstention/empty is ideal
        return (1.0 if len(hits) == 0 else 0.0, 0.0, 0.0)

    retrieved_ids = [c.chunk_id for c in hits]
    grades_map = {c.chunk_id: grade_chunk(c, query) for c in hits}

    # Grade >= 2 defines relevant passages (direct answer or essential supporting context)
    relevant_ids = {cid for cid, g in grades_map.items() if g >= 2}

    recall = compute_recall_at_k(retrieved_ids, relevant_ids, k=k) if relevant_ids else 0.0
    rr = compute_reciprocal_rank(retrieved_ids, relevant_ids, k=k) if relevant_ids else 0.0
    ndcg = compute_ndcg_at_k(retrieved_ids, grades_map, k=k)

    return (recall, rr, ndcg)


def run_retrieval_benchmark(
    retriever: HybridRetriever,
    user_id: str,
    dataset: list[EvalQuery],
    k: int = 5,
) -> BenchmarkReport:
    """Run ablation benchmark over the evaluation dataset across all 4 variants.

    Variants evaluated:
        1. 'dense' (Vector similarity)
        2. 'sparse' (BM25)
        3. 'fused' (RRF)
        4. 'reranked' (RRF + Cross-Encoder)

    Args:
        retriever: Configured HybridRetriever instance.
        user_id: Active user ID whose indexed documents are being searched.
        dataset: List of EvalQuery items.
        k: Cut-off rank for evaluation metrics (default: 5).

    Returns:
        BenchmarkReport with aggregated metrics across variants and categories.
    """
    variant_names = ["dense", "sparse", "fused", "reranked"]
    variant_scores: dict[str, list[tuple[float, float, float]]] = {v: [] for v in variant_names}
    variant_category_recalls: dict[str, dict[str, list[float]]] = {v: {} for v in variant_names}
    latencies: list[float] = []

    answerable_queries = [q for q in dataset if q.is_answerable]

    for q in dataset:
        start = time.perf_counter()
        debug_result = retriever.search_debug(user_id=user_id, query=q.query, limit=k)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        latencies.append(elapsed_ms)

        variant_hits: dict[str, list[RetrievedChunk] | list[RerankedChunk]] = {
            "dense": debug_result.dense_hits,
            "sparse": debug_result.sparse_hits,
            "fused": debug_result.fused_hits,
            "reranked": debug_result.reranked_hits,
        }

        if q.is_answerable:
            for v_name in variant_names:
                hits = variant_hits[v_name]
                recall, rr, ndcg = evaluate_hits(hits, q, k=k)
                variant_scores[v_name].append((recall, rr, ndcg))

                cat_dict = variant_category_recalls[v_name]
                if q.category not in cat_dict:
                    cat_dict[q.category] = []
                cat_dict[q.category].append(recall)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    num_answerable = len(answerable_queries)

    variants_metrics: dict[str, VariantMetrics] = {}
    for v_name in variant_names:
        scores = variant_scores[v_name]
        if num_answerable > 0 and scores:
            mean_recall = sum(s[0] for s in scores) / num_answerable
            mrr = sum(s[1] for s in scores) / num_answerable
            mean_ndcg = sum(s[2] for s in scores) / num_answerable
        else:
            mean_recall, mrr, mean_ndcg = 0.0, 0.0, 0.0

        cat_recall: dict[str, float] = {}
        for cat, rec_list in variant_category_recalls[v_name].items():
            cat_recall[cat] = sum(rec_list) / len(rec_list) if rec_list else 0.0

        variants_metrics[v_name] = VariantMetrics(
            variant_name=v_name,
            mean_recall_at_5=mean_recall,
            mrr=mrr,
            mean_ndcg_at_5=mean_ndcg,
            avg_latency_ms=avg_latency,
            category_recall=cat_recall,
        )

    return BenchmarkReport(
        total_queries=len(dataset),
        evaluated_answerable=num_answerable,
        unanswerable_count=len(dataset) - num_answerable,
        variants=variants_metrics,
    )
