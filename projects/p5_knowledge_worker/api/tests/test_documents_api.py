from knowledge_worker.api.deps import get_current_user_id
from tests.test_text import BIJOY

POLICY_MD = """# Leave Policy
Employees receive 20 days of annual leave. Unused days carry over for one year.

# ছুটির নীতিমালা
কর্মীরা বছরে ২০ দিন বার্ষিক ছুটি পাবেন। অব্যবহৃত ছুটি এক বছর পর্যন্ত জমা রাখা যাবে।
""".encode()


def upload(client, name="policy.md", data=POLICY_MD):
    return client.post("/api/v1/documents", files={"file": (name, data)})


def test_upload_indexes_into_db_qdrant_and_bm25(client, container):
    res = upload(client)
    assert res.status_code == 202
    doc_id = res.json()["id"]

    doc = client.get(f"/api/v1/documents/{doc_id}").json()
    assert doc["status"] == "indexed", doc["error_message"]
    assert doc["format"] == "md"
    assert doc["section_count"] == 2
    assert doc["language"] == "mixed"

    chunks = client.get(f"/api/v1/documents/{doc_id}/chunks").json()
    assert chunks["total"] == doc["chunk_count"] >= 2
    assert {c["heading"] for c in chunks["items"]} == {"Leave Policy", "ছুটির নীতিমালা"}
    assert {c["language"] for c in chunks["items"]} == {"en", "bn"}

    assert container.vectors.count("local") == doc["chunk_count"]
    bangla_hit = container.sparse.search("local", "ছুটি কত দিন", 1)[0]
    assert bangla_hit.chunk_id in {c["id"] for c in chunks["items"] if c["language"] == "bn"}


def test_list_is_paginated(client):
    upload(client, "a.md", b"# A\nalpha text here")
    upload(client, "b.md", b"# B\nbeta text here")
    page = client.get("/api/v1/documents", params={"limit": 1}).json()
    assert page["total"] == 2 and len(page["items"]) == 1
    assert client.get("/api/v1/documents", params={"limit": 101}).status_code == 422


def test_duplicate_upload_conflicts(client):
    first = upload(client).json()
    res = upload(client, name="copy.md")
    assert res.status_code == 409
    assert res.json()["details"]["document_id"] == first["id"]


def test_rejects_unsupported_and_oversized_files(client, container, monkeypatch):
    res = upload(client, "photo.png", b"\x89PNG\r\n\x1a\n")
    assert res.status_code == 415
    assert set(res.json()) == {"error", "message", "details"}

    monkeypatch.setattr(container.settings, "UPLOAD_MAX_BYTES", 10)
    assert upload(client, "big.md", b"x" * 11).status_code == 413


def test_bijoy_document_fails_with_actionable_message(client):
    doc_id = upload(client, "old.txt", BIJOY.encode()).json()["id"]
    doc = client.get(f"/api/v1/documents/{doc_id}").json()
    assert doc["status"] == "failed"
    assert "Bijoy" in doc["error_message"]
    assert doc["chunk_count"] == 0


def test_other_users_documents_are_404(client):
    doc_id = upload(client).json()["id"]
    client.app.dependency_overrides[get_current_user_id] = lambda: "someone-else"
    try:
        assert client.get(f"/api/v1/documents/{doc_id}").status_code == 404
        assert client.delete(f"/api/v1/documents/{doc_id}").status_code == 404
        assert client.get("/api/v1/documents").json()["total"] == 0
    finally:
        client.app.dependency_overrides.clear()


def test_delete_removes_vectors_chunks_bm25_and_file(client, container):
    doc_id = upload(client).json()["id"]
    stored = container.settings.upload_dir / "local" / f"{doc_id}.md"
    assert stored.exists()

    assert client.delete(f"/api/v1/documents/{doc_id}").status_code == 204
    assert client.get(f"/api/v1/documents/{doc_id}").status_code == 404
    assert container.vectors.count("local") == 0
    assert container.sparse.search("local", "leave", 5) == []
    assert not stored.exists()


def test_reindex_replaces_chunks(client, container):
    doc_id = upload(client).json()["id"]
    before = {c["id"] for c in client.get(f"/api/v1/documents/{doc_id}/chunks").json()["items"]}
    res = client.post(f"/api/v1/documents/{doc_id}/reindex")
    assert res.status_code == 202
    after = client.get(f"/api/v1/documents/{doc_id}/chunks").json()
    assert len(after["items"]) == len(before) and before.isdisjoint(c["id"] for c in after["items"])
    assert container.vectors.count("local") == len(before)


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_is_local_setting(container):
    assert container.settings.is_local is False  # ENVIRONMENT is "testing" in test suite
    container.settings.ENVIRONMENT = "development"
    assert container.settings.is_local is True
    container.settings.ENVIRONMENT = "local"
    assert container.settings.is_local is True
    container.settings.ENVIRONMENT = "production"
    assert container.settings.is_local is False
    container.settings.ENVIRONMENT = "testing"


def test_format_routes(client):
    from knowledge_worker.core.route_printer import format_routes
    routes = format_routes(client.app)
    paths = {r["path"] for r in routes}
    assert "/" in paths
    assert "/api/v1/documents" in paths
    assert "/health" in paths


def test_read_root(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Welcome to my FastAPI application!"
    assert data["title"] == "Enterprise Knowledge Worker API"
    assert data["meta_title"] == "Enterprise Knowledge Worker API"
    assert "version" in data
    assert "docs" in data

    # Test HTML response when requested by a browser
    html_res = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert html_res.status_code == 200
    assert "<title>Enterprise Knowledge Worker API</title>" in html_res.text
    assert '<meta name="title" content="Enterprise Knowledge Worker API">' in html_res.text

