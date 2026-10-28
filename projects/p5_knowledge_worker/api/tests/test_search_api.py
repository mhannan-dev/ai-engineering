"""Integration tests for Search API endpoints."""

import pytest

from knowledge_worker.db.models import ChunkModel, DocumentModel
from knowledge_worker.db.session import SessionLocal
from knowledge_worker.ingestion.vector_store import VectorPoint

DOC_ID = "00000000-0000-0000-0000-000000000001"
CHUNK_AI_ID = "00000000-0000-0000-0000-000000000011"
CHUNK_LEAVE_ID = "00000000-0000-0000-0000-000000000012"


@pytest.fixture
def seeded_client(client, container):
    """Seed documents into test database and indices."""
    doc = DocumentModel(
        id=DOC_ID,
        user_id="local",
        filename="company_handbook.md",
        format="md",
        size_bytes=1000,
        sha256="fakehash001",
        stored_path="fake/path.md",
        status="indexed",
        language="mixed",
        section_count=2,
        chunk_count=2,
    )
    chunk1 = ChunkModel(
        id=CHUNK_AI_ID,
        document_id=DOC_ID,
        user_id="local",
        ordinal=0,
        page=1,
        heading="প্রযুক্তি ও এআই",
        language="bn",
        token_count=40,
        text="কোম্পানিতে কৃত্রিম বুদ্ধিমত্তা ও ক্লাউড প্রযুক্তি নিয়ে নতুন রিসার্চ টিম গঠন করা হয়েছে।",
    )
    chunk2 = ChunkModel(
        id=CHUNK_LEAVE_ID,
        document_id=DOC_ID,
        user_id="local",
        ordinal=1,
        page=2,
        heading="Annual Leave",
        language="en",
        token_count=35,
        text="Employees receive 20 days of annual leave each year with full compensation.",
    )

    with SessionLocal() as db:
        db.add_all([doc, chunk1, chunk2])
        db.commit()

    points = [
        VectorPoint(
            chunk_id=chunk1.id,
            document_id=chunk1.document_id,
            user_id=chunk1.user_id,
            vector=container.embedder._vector(chunk1.text),
        ),
        VectorPoint(
            chunk_id=chunk2.id,
            document_id=chunk2.document_id,
            user_id=chunk2.user_id,
            vector=container.embedder._vector(chunk2.text),
        ),
    ]
    container.vectors.upsert(points)

    container.sparse.rebuild(
        "local",
        [(chunk1.id, chunk1.text), (chunk2.id, chunk2.text)],
    )

    return client


def test_search_banglish_query(seeded_client):
    response = seeded_client.post(
        "/api/v1/search",
        json={"query": "krittim buddhimotta", "limit": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["was_banglish"] is True
    assert data["normalized_query"] == "কৃত্রিম বুদ্ধিমত্তা"
    assert data["total"] > 0
    top = data["results"][0]
    assert top["chunk_id"] == CHUNK_AI_ID
    assert "কৃত্রিম বুদ্ধিমত্তা" in top["text"]
    assert top["document_filename"] == "company_handbook.md"


def test_search_english_query(seeded_client):
    response = seeded_client.post(
        "/api/v1/search",
        json={"query": "annual leave", "limit": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["was_banglish"] is False
    assert data["total"] > 0
    top = data["results"][0]
    assert top["chunk_id"] == CHUNK_LEAVE_ID
    assert "annual leave" in top["text"].lower()


def test_search_debug_endpoint(seeded_client):
    response = seeded_client.get(
        "/api/v1/search/debug",
        params={"query": "krittim buddhimotta", "limit": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["was_banglish"] is True
    assert data["normalized_query"] == "কৃত্রিম বুদ্ধিমত্তা"
    assert "fused_hits" in data
    assert "dense_hits" in data
    assert "sparse_hits" in data
    assert len(data["fused_hits"]) > 0
    assert "reranked_hits" in data


def test_search_abstention_on_unrelated_query(seeded_client):
    # Query completely unrelated to HR handbook with strict threshold
    response = seeded_client.post(
        "/api/v1/search",
        json={"query": "potato farming on mars", "limit": 5, "threshold": 0.8},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_abstention"] is True
