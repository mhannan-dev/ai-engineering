"""Tests for HybridRetriever (Dense + Sparse + RRF + Banglish normalization)."""

import pytest

from knowledge_worker.db.models import ChunkModel, DocumentModel
from knowledge_worker.db.session import SessionLocal
from knowledge_worker.ingestion.vector_store import VectorPoint
from knowledge_worker.retrieval.retriever import HybridRetriever, RetrievedChunk, SearchDebugResult

DOC1_ID = "00000000-0000-0000-0000-000000000001"
CHUNK1_1_ID = "00000000-0000-0000-0000-000000000011"
CHUNK1_2_ID = "00000000-0000-0000-0000-000000000012"

DOC2_ID = "00000000-0000-0000-0000-000000000002"
CHUNK2_1_ID = "00000000-0000-0000-0000-000000000021"
CHUNK2_2_ID = "00000000-0000-0000-0000-000000000022"


@pytest.fixture
def populated_container(container):
    """Seed documents for retrieval testing."""
    # Create Document 1 (English leave policy)
    doc1 = DocumentModel(
        id=DOC1_ID,
        user_id="default_user",
        filename="leave_policy.md",
        format="md",
        size_bytes=500,
        sha256="fakehash1",
        stored_path="fake/path1.md",
        status="indexed",
        language="en",
        section_count=1,
        chunk_count=2,
    )
    chunk1_1 = ChunkModel(
        id=CHUNK1_1_ID,
        document_id=DOC1_ID,
        user_id="default_user",
        ordinal=0,
        page=1,
        heading="Annual Leave",
        language="en",
        token_count=30,
        text="Employees receive 20 days of paid annual leave per year.",
    )
    chunk1_2 = ChunkModel(
        id=CHUNK1_2_ID,
        document_id=DOC1_ID,
        user_id="default_user",
        ordinal=1,
        page=1,
        heading="Sick Leave",
        language="en",
        token_count=30,
        text="Sick leave requires a medical certificate if longer than 3 days.",
    )

    # Create Document 2 (Bangla tech & summit)
    doc2 = DocumentModel(
        id=DOC2_ID,
        user_id="default_user",
        filename="bangladesh_japan.md",
        format="md",
        size_bytes=1000,
        sha256="fakehash2",
        stored_path="fake/path2.md",
        status="indexed",
        language="bn",
        section_count=1,
        chunk_count=2,
    )
    chunk2_1 = ChunkModel(
        id=CHUNK2_1_ID,
        document_id=DOC2_ID,
        user_id="default_user",
        ordinal=0,
        page=1,
        heading="প্রযুক্তি ও এআই পার্ক",
        language="bn",
        token_count=45,
        text="প্রস্তাবিত টেক পার্কে কৃত্রিম বুদ্ধিমত্তা (এআই) এবং ক্লাউড কম্পিউটিং প্রাধান্য পাবে।",
    )
    chunk2_2 = ChunkModel(
        id=CHUNK2_2_ID,
        document_id=DOC2_ID,
        user_id="default_user",
        ordinal=1,
        page=2,
        heading="বিনিয়োগ পরিকল্পনা",
        language="bn",
        token_count=50,
        text="জাপান বাংলাদেশে ১ ট্রিলিয়ন জাপানি ইয়েন বেসরকারি বিনিয়োগ নিয়ে আলোচনা করেছে।",
    )

    with SessionLocal() as db:
        db.add_all([doc1, doc2, chunk1_1, chunk1_2, chunk2_1, chunk2_2])
        db.commit()

    # Index into Vector Store
    points = [
        VectorPoint(
            chunk_id=chunk1_1.id,
            document_id=chunk1_1.document_id,
            user_id=chunk1_1.user_id,
            vector=container.embedder._vector(chunk1_1.text),
        ),
        VectorPoint(
            chunk_id=chunk1_2.id,
            document_id=chunk1_2.document_id,
            user_id=chunk1_2.user_id,
            vector=container.embedder._vector(chunk1_2.text),
        ),
        VectorPoint(
            chunk_id=chunk2_1.id,
            document_id=chunk2_1.document_id,
            user_id=chunk2_1.user_id,
            vector=container.embedder._vector(chunk2_1.text),
        ),
        VectorPoint(
            chunk_id=chunk2_2.id,
            document_id=chunk2_2.document_id,
            user_id=chunk2_2.user_id,
            vector=container.embedder._vector(chunk2_2.text),
        ),
    ]
    container.vectors.upsert(points)

    # Index into BM25 Sparse Index
    container.sparse.rebuild(
        "default_user",
        [
            (chunk1_1.id, chunk1_1.text),
            (chunk1_2.id, chunk1_2.text),
            (chunk2_1.id, chunk2_1.text),
            (chunk2_2.id, chunk2_2.text),
        ],
    )

    return container


class TestHybridRetriever:
    def test_retrieve_bangla_query(self, populated_container):
        retriever = HybridRetriever(
            SessionLocal,
            populated_container.embedder,
            populated_container.vectors,
            populated_container.sparse,
        )
        results = retriever.retrieve("default_user", "কৃত্রিম বুদ্ধিমত্তা")
        assert len(results) > 0
        top = results[0]
        assert isinstance(top, RetrievedChunk)
        assert top.chunk_id == CHUNK2_1_ID
        assert top.document_filename == "bangladesh_japan.md"
        assert "কৃত্রিম বুদ্ধিমত্তা" in top.text
        assert top.score > 0

    def test_retrieve_banglish_query_normalizes_and_finds_match(self, populated_container):
        retriever = HybridRetriever(
            SessionLocal,
            populated_container.embedder,
            populated_container.vectors,
            populated_container.sparse,
        )
        # Banglish query should be transliterated to "কৃত্রিম বুদ্ধিমত্তা"
        results = retriever.retrieve("default_user", "krittim buddhimotta")
        assert len(results) > 0
        top = results[0]
        assert top.chunk_id == CHUNK2_1_ID
        assert "কৃত্রিম বুদ্ধিমত্তা" in top.text

    def test_retrieve_english_query(self, populated_container):
        retriever = HybridRetriever(
            SessionLocal,
            populated_container.embedder,
            populated_container.vectors,
            populated_container.sparse,
        )
        results = retriever.retrieve("default_user", "annual leave days")
        assert len(results) > 0
        top = results[0]
        assert top.chunk_id == CHUNK1_1_ID
        assert top.document_filename == "leave_policy.md"

    def test_search_debug_returns_side_by_side_breakdown(self, populated_container):
        retriever = HybridRetriever(
            SessionLocal,
            populated_container.embedder,
            populated_container.vectors,
            populated_container.sparse,
        )
        debug = retriever.search_debug("default_user", "krittim buddhimotta")
        assert isinstance(debug, SearchDebugResult)
        assert debug.was_banglish is True
        assert debug.normalized_query == "কৃত্রিম বুদ্ধিমত্তা"
        assert len(debug.fused_hits) > 0
        assert debug.fused_hits[0].chunk_id == CHUNK2_1_ID



class TestSearchDebugRerankPool:
    def test_rerank_sees_more_than_the_returned_fused_hits(self, populated_container):
        # limit=1 returns one fused hit, but the reranker still ranks the wider pool, like
        # retrieve_and_rerank does in production.
        retriever = HybridRetriever(
            SessionLocal, populated_container.embedder, populated_container.vectors,
            populated_container.sparse, reranker=populated_container.reranker,
        )
        debug = retriever.search_debug("default_user", "sick leave certificate", limit=1, threshold=0.0)
        assert len(debug.fused_hits) == 1
        assert [c.chunk_id for c in debug.reranked_hits] == [CHUNK1_2_ID]
