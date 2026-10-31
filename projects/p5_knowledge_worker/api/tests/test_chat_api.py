"""Integration tests for Chat & Faithful Generation API endpoints."""

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
            user_id="local",
            vector=container.embedder.embed_query(chunk1.text),
        ),
        VectorPoint(
            chunk_id=chunk2.id,
            document_id=chunk2.document_id,
            user_id="local",
            vector=container.embedder.embed_query(chunk2.text),
        ),
    ]
    container.vectors.upsert(points)
    container.sparse.rebuild("local", [(c.id, c.text) for c in [chunk1, chunk2]])

    return client


def test_chat_generation_endpoint(seeded_client):
    payload = {
        "query": "How many days of annual leave do employees receive?",
        "top_k": 3,
        "threshold": 0.1,
    }
    response = seeded_client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["query"] == payload["query"]
    assert "answer" in data
    assert "citations" in data
    assert "validation" in data
    assert "sources" in data
    assert len(data["sources"]) > 0
    assert data["is_abstention"] is False


def test_chat_generation_abstention(seeded_client):
    payload = {
        "query": "Completely unrelated astrophysical telescope query",
        "top_k": 3,
        "threshold": 0.99,  # High threshold triggers abstention
    }
    response = seeded_client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["is_abstention"] is True
    assert "not contain sufficient information" in data["answer"]
    assert data["citations"] == []


def test_chat_streaming_post_endpoint(seeded_client):
    payload = {
        "query": "annual leave",
        "top_k": 2,
        "threshold": 0.1,
    }
    response = seeded_client.post("/api/v1/chat/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body = response.text
    assert "event: status" in body
    assert "event: sources" in body
    assert "event: token" in body
    assert "event: done" in body


def test_chat_stream_has_no_get_variant(seeded_client):
    # A GET stream would need the token in the URL (EventSource can't send headers),
    # which leaks it into logs and history. Only POST is served.
    response = seeded_client.get("/api/v1/chat/stream?query=annual+leave")
    assert response.status_code == 405
