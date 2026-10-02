"""Integration tests for health, diagnostic, and echo endpoints."""


def test_root_health_check(client):
    """Verify root / endpoint returns health status ok and version."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_health_check(client):
    """Verify health endpoint returns status ok and version."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_echo_endpoint(client):
    """Verify echo endpoint correctly computes message length."""
    payload = {"message": "Test layered architecture!"}
    response = client.post("/echo", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["you_said"] == payload["message"]
    assert data["length"] == len(payload["message"])
