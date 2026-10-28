"""Schemas for Hybrid Search and Debug endpoints."""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query in English, Bangla, or Banglish")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of chunks to return")
    rerank: bool = Field(default=True, description="Whether to apply cross-encoder reranking (Phase 3)")
    threshold: float | None = Field(default=None, description="Optional custom abstention threshold (e.g. 0.25)")


class SearchResultChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_filename: str
    page: int | None = None
    heading: str | None = None
    text: str
    score: float
    dense_rank: int | None = None
    sparse_rank: int | None = None
    fused_rank: int | None = None
    rerank_rank: int | None = None


class SearchResponse(BaseModel):
    query: str
    normalized_query: str
    was_banglish: bool
    is_abstention: bool = False
    reranked: bool = False
    total: int
    results: list[SearchResultChunk]


class SearchDebugResponse(BaseModel):
    query: str
    normalized_query: str
    was_banglish: bool
    dense_hits: list[SearchResultChunk]
    sparse_hits: list[SearchResultChunk]
    fused_hits: list[SearchResultChunk]
    reranked_hits: list[SearchResultChunk] = []
