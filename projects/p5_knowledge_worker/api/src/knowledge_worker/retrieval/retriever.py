from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from knowledge_worker.db.models import ChunkModel, DocumentModel
from knowledge_worker.ingestion.sparse_index import SparseIndex
from knowledge_worker.ingestion.vector_store import VectorStore
from knowledge_worker.retrieval.fusion import reciprocal_rank_fusion
from knowledge_worker.retrieval.models import (
    QueryEmbedder,
    RerankedChunk,
    Reranker,
    RerankResult,
    RetrievedChunk,
    SearchDebugResult,
)
from knowledge_worker.retrieval.reranker import rerank_candidates
from knowledge_worker.text.banglish import normalize_query


class HybridRetriever:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        embedder: QueryEmbedder,
        vectors: VectorStore,
        sparse: SparseIndex,
        reranker: Reranker | None = None,
    ):
        self._sessions = session_factory
        self._embedder = embedder
        self._vectors = vectors
        self._sparse = sparse
        self._reranker = reranker

    def retrieve(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
        dense_limit: int = 20,
        sparse_limit: int = 20,
        rrf_k: int = 60,
    ) -> list[RetrievedChunk]:
        """Perform hybrid search over user's indexed documents.

        1. Normalize query using `normalize_query(query)` (handling Banglish if present).
        2. Retrieve top `dense_limit` chunk ids from Qdrant via `self._vectors.search`.
        3. Retrieve top `sparse_limit` chunk ids from BM25 via `self._sparse.search`.
        4. Fuse rankings using `reciprocal_rank_fusion`.
        5. Fetch chunk details & document filenames from DB for the fused chunk ids.
        6. Return `list[RetrievedChunk]` ordered by descending fused score.
        """
        normalized_query, _ = normalize_query(query)
        if not normalized_query.strip():
            return []

        # 1. Dense search ("ভাবুক ভাই")
        query_vector = self._embedder.embed_query(normalized_query)
        dense_results = self._vectors.search(user_id, query_vector, limit=dense_limit)
        dense_ids = [hit.chunk_id for hit in dense_results]
        dense_ranks = {hit.chunk_id: rank for rank, hit in enumerate(dense_results, start=1)}

        # 2. Sparse search ("আক্ষরিক আপা")
        sparse_results = self._sparse.search(user_id, normalized_query, limit=sparse_limit)
        sparse_ids = [hit.chunk_id for hit in sparse_results]
        sparse_ranks = {hit.chunk_id: rank for rank, hit in enumerate(sparse_results, start=1)}

        # 3. Reciprocal Rank Fusion (RRF)
        fused = reciprocal_rank_fusion([dense_ids, sparse_ids], k=rrf_k, limit=limit)
        if not fused:
            return []

        fused_scores = dict(fused)
        fused_ids = [chunk_id for chunk_id, _ in fused]

        # 4. Fetch chunk records from DB
        chunks_by_id = self._fetch_chunks(user_id, fused_ids)

        # 5. Build ordered RetrievedChunk results
        results: list[RetrievedChunk] = []
        for chunk_id in fused_ids:
            if chunk_id in chunks_by_id:
                chunk, filename = chunks_by_id[chunk_id]
                results.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        document_filename=filename,
                        page=chunk.page,
                        heading=chunk.heading,
                        text=chunk.text,
                        score=fused_scores[chunk_id],
                        dense_rank=dense_ranks.get(chunk_id),
                        sparse_rank=sparse_ranks.get(chunk_id),
                    )
                )

        return results

    def retrieve_and_rerank(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        candidate_limit: int = 20,
        threshold: float = 0.25,
        rrf_k: int = 60,
    ) -> RerankResult:
        """Retrieve hybrid candidates and rerank with cross-encoder, enforcing abstention threshold."""
        normalized_query, was_banglish = normalize_query(query)
        candidates = self.retrieve(
            user_id=user_id,
            query=query,
            limit=candidate_limit,
            dense_limit=candidate_limit,
            sparse_limit=candidate_limit,
            rrf_k=rrf_k,
        )

        if not candidates or self._reranker is None:
            # Without reranker, fallback directly to fused ranking
            chunks = [
                RerankedChunk(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    document_filename=c.document_filename,
                    page=c.page,
                    heading=c.heading,
                    text=c.text,
                    score=c.score,
                    fused_rank=i,
                    rerank_rank=i,
                )
                for i, c in enumerate(candidates[:limit], start=1)
            ]
            return RerankResult(
                query=query,
                normalized_query=normalized_query,
                was_banglish=was_banglish,
                is_abstention=len(chunks) == 0,
                threshold=threshold,
                chunks=chunks,
            )

        return rerank_candidates(
            query=query,
            candidates=candidates,
            reranker=self._reranker,
            threshold=threshold,
            limit=limit,
            was_banglish=was_banglish,
            normalized_query=normalized_query,
        )

    def search_debug(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
        dense_limit: int = 20,
        sparse_limit: int = 20,
        rrf_k: int = 60,
        threshold: float = 0.25,
    ) -> SearchDebugResult:
        """Return dense, sparse, fused, and reranked hits side-by-side for inspection & ablation."""
        normalized_query, was_banglish = normalize_query(query)
        if not normalized_query.strip():
            return SearchDebugResult(
                query=query,
                normalized_query=normalized_query,
                was_banglish=was_banglish,
                dense_hits=[],
                sparse_hits=[],
                fused_hits=[],
                reranked_hits=[],
            )

        # 1. Dense search
        query_vector = self._embedder.embed_query(normalized_query)
        dense_results = self._vectors.search(user_id, query_vector, limit=dense_limit)
        dense_ids = [hit.chunk_id for hit in dense_results]
        dense_ranks = {hit.chunk_id: rank for rank, hit in enumerate(dense_results, start=1)}

        # 2. Sparse search
        sparse_results = self._sparse.search(user_id, normalized_query, limit=sparse_limit)
        sparse_ids = [hit.chunk_id for hit in sparse_results]
        sparse_ranks = {hit.chunk_id: rank for rank, hit in enumerate(sparse_results, start=1)}

        # 3. RRF Fusion
        fused = reciprocal_rank_fusion([dense_ids, sparse_ids], k=rrf_k, limit=limit)
        fused_scores = dict(fused)
        fused_ids = [chunk_id for chunk_id, _ in fused]

        # 4. Fetch DB records for all chunks
        all_ids = list(dict.fromkeys(dense_ids + sparse_ids + fused_ids))
        chunks_by_id = self._fetch_chunks(user_id, all_ids)

        def make_retrieved(
            cid: str, score: float, d_rank: int | None = None, s_rank: int | None = None
        ) -> RetrievedChunk | None:
            if cid not in chunks_by_id:
                return None
            chunk, filename = chunks_by_id[cid]
            return RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_filename=filename,
                page=chunk.page,
                heading=chunk.heading,
                text=chunk.text,
                score=score,
                dense_rank=d_rank,
                sparse_rank=s_rank,
            )

        dense_hits = [
            hit
            for r in dense_results
            if (hit := make_retrieved(r.chunk_id, r.score, d_rank=dense_ranks.get(r.chunk_id)))
            is not None
        ]
        sparse_hits = [
            hit
            for r in sparse_results
            if (hit := make_retrieved(r.chunk_id, r.score, s_rank=sparse_ranks.get(r.chunk_id)))
            is not None
        ]
        fused_hits = [
            hit
            for cid in fused_ids
            if (
                hit := make_retrieved(
                    cid,
                    fused_scores[cid],
                    d_rank=dense_ranks.get(cid),
                    s_rank=sparse_ranks.get(cid),
                )
            )
            is not None
        ]

        # 5. Reranked hits (if reranker is present)
        reranked_hits: list[RerankedChunk] = []
        if self._reranker is not None and fused_hits:
            rerank_res = rerank_candidates(
                query=query,
                candidates=fused_hits,
                reranker=self._reranker,
                threshold=threshold,
                limit=limit,
                was_banglish=was_banglish,
                normalized_query=normalized_query,
            )
            reranked_hits = rerank_res.chunks

        return SearchDebugResult(
            query=query,
            normalized_query=normalized_query,
            was_banglish=was_banglish,
            dense_hits=dense_hits,
            sparse_hits=sparse_hits,
            fused_hits=fused_hits,
            reranked_hits=reranked_hits,
        )

    def _fetch_chunks(
        self, user_id: str, chunk_ids: list[str]
    ) -> dict[str, tuple[ChunkModel, str]]:
        if not chunk_ids:
            return {}

        with self._sessions() as db:
            stmt = (
                select(ChunkModel, DocumentModel.filename)
                .join(DocumentModel, ChunkModel.document_id == DocumentModel.id)
                .where(
                    ChunkModel.user_id == user_id,
                    ChunkModel.id.in_(chunk_ids),
                )
            )
            rows = db.execute(stmt).all()
            return {chunk.id: (chunk, filename) for chunk, filename in rows}
