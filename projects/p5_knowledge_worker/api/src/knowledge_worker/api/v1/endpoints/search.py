"""Hybrid Search and Debug endpoints."""

from typing import Annotated

from fastapi import APIRouter, Query

from knowledge_worker.api.deps import ContainerDep, CurrentUserIdDep
from knowledge_worker.schemas.search import (
    SearchDebugResponse,
    SearchRequest,
    SearchResponse,
    SearchResultChunk,
)
from knowledge_worker.text.banglish import normalize_query

router = APIRouter()


@router.post(
    "",
    response_model=SearchResponse,
    summary="Hybrid search over indexed documents",
    description="Fuses dense vector search (Qdrant) and sparse keyword search (BM25) via RRF with optional Cross-Encoder reranking.",
)
def search_documents(
    payload: SearchRequest,
    user_id: CurrentUserIdDep,
    container: ContainerDep,
) -> SearchResponse:
    threshold = (
        payload.threshold
        if payload.threshold is not None
        else container.settings.RERANKER_THRESHOLD
    )

    if payload.rerank:
        rerank_res = container.retriever.retrieve_and_rerank(
            user_id=user_id,
            query=payload.query,
            limit=payload.limit,
            candidate_limit=container.settings.RERANKER_CANDIDATE_LIMIT,
            threshold=threshold,
        )
        results = [
            SearchResultChunk(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                document_filename=c.document_filename,
                page=c.page,
                heading=c.heading,
                text=c.text,
                score=c.score,
                fused_rank=c.fused_rank,
                rerank_rank=c.rerank_rank,
            )
            for c in rerank_res.chunks
        ]
        return SearchResponse(
            query=payload.query,
            normalized_query=rerank_res.normalized_query,
            was_banglish=rerank_res.was_banglish,
            is_abstention=rerank_res.is_abstention,
            reranked=True,
            total=len(results),
            results=results,
        )

    # Standard hybrid retrieval without cross-encoder
    normalized_query, was_banglish = normalize_query(payload.query)
    retrieved = container.retriever.retrieve(
        user_id=user_id,
        query=payload.query,
        limit=payload.limit,
    )
    results = [
        SearchResultChunk(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            document_filename=c.document_filename,
            page=c.page,
            heading=c.heading,
            text=c.text,
            score=c.score,
            dense_rank=c.dense_rank,
            sparse_rank=c.sparse_rank,
        )
        for c in retrieved
    ]
    return SearchResponse(
        query=payload.query,
        normalized_query=normalized_query,
        was_banglish=was_banglish,
        is_abstention=len(results) == 0,
        reranked=False,
        total=len(results),
        results=results,
    )


@router.get(
    "/debug",
    response_model=SearchDebugResponse,
    summary="Inspect Dense, Sparse, Fused, and Reranked search results side-by-side",
    description="Returns detailed ranking breakdown of Dense, BM25, fused RRF, and cross-encoder reranked results for query ablation.",
)
def search_debug(
    query: Annotated[str, Query(min_length=1, max_length=1000)],
    user_id: CurrentUserIdDep,
    container: ContainerDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    threshold: Annotated[float, Query(ge=0.0, le=1.0)] = 0.25,
) -> SearchDebugResponse:
    debug_result = container.retriever.search_debug(
        user_id=user_id,
        query=query,
        limit=limit,
        threshold=threshold,
    )

    def to_schema(c) -> SearchResultChunk:
        return SearchResultChunk(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            document_filename=c.document_filename,
            page=c.page,
            heading=c.heading,
            text=c.text,
            score=c.score,
            dense_rank=getattr(c, "dense_rank", None),
            sparse_rank=getattr(c, "sparse_rank", None),
            fused_rank=getattr(c, "fused_rank", None),
            rerank_rank=getattr(c, "rerank_rank", None),
        )

    return SearchDebugResponse(
        query=debug_result.query,
        normalized_query=debug_result.normalized_query,
        was_banglish=debug_result.was_banglish,
        dense_hits=[to_schema(c) for c in debug_result.dense_hits],
        sparse_hits=[to_schema(c) for c in debug_result.sparse_hits],
        fused_hits=[to_schema(c) for c in debug_result.fused_hits],
        reranked_hits=[to_schema(c) for c in debug_result.reranked_hits],
    )
