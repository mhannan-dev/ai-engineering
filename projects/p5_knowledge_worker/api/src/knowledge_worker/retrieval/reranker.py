"""Cross-encoder reranking and relevance thresholding (Phase 3).

Reranks candidate passages retrieved by hybrid search (Phase 2) using a multilingual
cross-encoder. Scores pairwise relevance (Query + Passage) and rejects unanswerable
queries when the top relevance score falls below the threshold ("I don't know").
"""

import threading
from pathlib import Path

from knowledge_worker.retrieval.models import (
    RerankedChunk,
    Reranker,
    RerankResult,
    RetrievedChunk,
)


class FastEmbedReranker:
    """Production cross-encoder using fastembed and Jina v2 multilingual reranker."""

    def __init__(
        self,
        model_name: str = "jinaai/jina-reranker-v2-base-multilingual",
        cache_dir: str | Path | None = None,
    ):
        self.model_name = model_name
        self.cache_dir = str(cache_dir) if cache_dir else None
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is None:
                from fastembed.rerank.cross_encoder import TextCrossEncoder

                self._model = TextCrossEncoder(self.model_name, cache_dir=self.cache_dir)
        return self._model

    def rerank(self, query: str, passages: list[str]) -> list[float]:
        if not passages:
            return []
        model = self._load()
        import math

        # Cross-encoder ONNX output is raw logits; map to [0.0, 1.0] via sigmoid
        return [1.0 / (1.0 + math.exp(-float(s))) for s in model.rerank(query, passages)]


def rerank_candidates(
    query: str,
    candidates: list[RetrievedChunk],
    reranker: Reranker,
    threshold: float = 0.25,
    limit: int = 5,
    was_banglish: bool = False,
    normalized_query: str | None = None,
) -> RerankResult:
    """Rerank hybrid retrieval candidate chunks with a cross-encoder.

    Rules:
    1. If `candidates` is empty, return an abstention (`is_abstention=True`, `chunks=[]`).
    2. Pass `(normalized_query or query)` and all candidate `text`s to `reranker.rerank(...)`.
    3. Pair each candidate with its cross-encoder score and sort descending by score.
    4. Break ties deterministically by chunk_id ascending.
    5. Check if the highest score is strictly below `threshold`. If so:
       mark `is_abstention=True` (the system abstains: "I don't know").
       Otherwise `is_abstention=False`.
    6. Apply `limit` to the reranked list.
    7. Populate `rerank_rank` (1-indexed) and preserve original `fused_rank` (1-indexed).
    8. Return `RerankResult`.
    """
    norm_q = normalized_query or query
    if not candidates:
        return RerankResult(
            query=query,
            normalized_query=norm_q,
            was_banglish=was_banglish,
            is_abstention=True,
            threshold=threshold,
            chunks=[],
        )

    # 1. Evaluate cross-encoder pairwise scores
    passages = [c.text for c in candidates]
    scores = list(reranker.rerank(norm_q, passages))

    # 2. Pair candidate with original fused rank (1-based) and cross-encoder score
    scored: list[tuple[RetrievedChunk, int, float]] = [
        (candidate, rank, score)
        for rank, (candidate, score) in enumerate(zip(candidates, scores, strict=True), start=1)
    ]

    # 3. Sort by score descending, tie-break by chunk_id ascending
    scored.sort(key=lambda item: (-item[2], item[0].chunk_id))

    # 4. Check abstention threshold ("I don't know")
    top_score = scored[0][2]
    is_abstention = bool(top_score < threshold)

    # 5. Apply limit
    if limit is not None and limit >= 0:
        scored = scored[:limit]

    # 6. Build RerankedChunk list with 1-indexed rerank_rank
    reranked_chunks: list[RerankedChunk] = [
        RerankedChunk(
            chunk_id=candidate.chunk_id,
            document_id=candidate.document_id,
            document_filename=candidate.document_filename,
            page=candidate.page,
            heading=candidate.heading,
            text=candidate.text,
            score=float(score),
            fused_rank=fused_rank,
            rerank_rank=rerank_rank,
        )
        for rerank_rank, (candidate, fused_rank, score) in enumerate(scored, start=1)
    ]

    return RerankResult(
        query=query,
        normalized_query=norm_q,
        was_banglish=was_banglish,
        is_abstention=is_abstention,
        threshold=threshold,
        chunks=reranked_chunks,
    )
