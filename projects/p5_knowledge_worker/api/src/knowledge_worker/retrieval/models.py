"""Data models and protocols for retrieval, fusion, and reranking."""

from dataclasses import dataclass, field
from typing import Protocol


class QueryEmbedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...


class Reranker(Protocol):
    def rerank(self, query: str, passages: list[str]) -> list[float]: ...


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_filename: str
    page: int | None
    heading: str | None
    text: str
    score: float
    dense_rank: int | None = None
    sparse_rank: int | None = None


@dataclass(frozen=True)
class RerankedChunk:
    chunk_id: str
    document_id: str
    document_filename: str
    page: int | None
    heading: str | None
    text: str
    score: float
    fused_rank: int
    rerank_rank: int


@dataclass(frozen=True)
class RerankResult:
    query: str
    normalized_query: str
    was_banglish: bool
    is_abstention: bool
    threshold: float
    chunks: list[RerankedChunk]


@dataclass(frozen=True)
class SearchDebugResult:
    query: str
    normalized_query: str
    was_banglish: bool
    dense_hits: list[RetrievedChunk]
    sparse_hits: list[RetrievedChunk]
    fused_hits: list[RetrievedChunk]
    reranked_hits: list[RerankedChunk] = field(default_factory=list)
