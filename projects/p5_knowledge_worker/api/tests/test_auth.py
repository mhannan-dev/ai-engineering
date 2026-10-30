import base64
import json
import time

import pytest
from fastapi.testclient import TestClient

from knowledge_worker.config import get_settings
from knowledge_worker.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from knowledge_worker.main import create_app

SECRET = "test-secret"


class TestPasswords:
    def test_round_trip(self):
        hashed = hash_password("correct horse")
        assert verify_password("correct horse", hashed)
        assert not verify_password("wrong horse", hashed)

    def test_same_password_gets_different_salts(self):
        assert hash_password("same-password") != hash_password("same-password")

    def test_malformed_hash_is_rejected(self):
        assert not verify_password("anything", "no-dollar-sign")


class TestTokens:
    def test_round_trip(self):
        claims = decode_access_token(create_access_token("user-1", SECRET), SECRET)
        assert claims is not None and claims["sub"] == "user-1"

    def test_wrong_secret_is_rejected(self):
        assert decode_access_token(create_access_token("user-1", SECRET), "other") is None

    def test_expired_is_rejected(self):
        assert decode_access_token(create_access_token("user-1", SECRET, expires_minutes=-1), SECRET) is None

    def test_tampered_payload_is_rejected(self):
        header, _, signature = create_access_token("user-1", SECRET).split(".")
        forged = base64.urlsafe_b64encode(
            json.dumps({"sub": "admin", "exp": int(time.time()) + 60}).encode()
        ).decode().rstrip("=")
        assert decode_access_token(f"{header}.{forged}.{signature}", SECRET) is None

    @pytest.mark.parametrize("token", ["", "a.b", "a.b.c", "not a token"])
    def test_garbage_is_rejected(self, token):
        assert decode_access_token(token, SECRET) is None


@pytest.fixture
def auth_client(container):
    """An app with sign-in required, sharing the test container."""
    settings = get_settings().model_copy(update={"AUTH_ENABLED": True})
    app = create_app(lambda: container)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as client:
        yield client


def register(client, email="rahim@example.com", password="password123", name="Rahim"):
    return client.post(
        "/api/v1/auth/register", json={"email": email, "name": name, "password": password}
    )


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestAuthApi:
    def test_config_reports_enabled(self, auth_client, client):
        assert auth_client.get("/api/v1/auth/config").json() == {"enabled": True}
        assert client.get("/api/v1/auth/config").json() == {"enabled": False}

    def test_register_returns_token_and_user(self, auth_client):
        response = register(auth_client)
        assert response.status_code == 201
        body = response.json()
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "rahim@example.com"
        assert "hashed_password" not in body["user"]

        me = auth_client.get("/api/v1/auth/me", headers=bearer(body["access_token"]))
        assert me.status_code == 200
        assert me.json()["name"] == "Rahim"

    def test_duplicate_email_is_case_insensitive(self, auth_client):
        assert register(auth_client).status_code == 201
        response = register(auth_client, email="RAHIM@example.com")
        assert response.status_code == 409
        assert response.json()["error"] == "ConflictError"

    @pytest.mark.parametrize(
        "payload",
        [
            {"email": "not-an-email", "name": "A", "password": "password123"},
            {"email": "a@example.com", "name": "A", "password": "short"},
            {"email": "a@example.com", "name": "", "password": "password123"},
        ],
    )
    def test_register_validation(self, auth_client, payload):
        assert auth_client.post("/api/v1/auth/register", json=payload).status_code == 422

    def test_login(self, auth_client):
        register(auth_client)
        response = auth_client.post(
            "/api/v1/auth/login", json={"email": "Rahim@Example.com", "password": "password123"}
        )
        assert response.status_code == 200
        assert response.json()["access_token"]

    @pytest.mark.parametrize(
        "email,password", [("rahim@example.com", "wrong-password"), ("nobody@example.com", "password123")]
    )
    def test_login_failure_has_one_message(self, auth_client, email, password):
        register(auth_client)
        response = auth_client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 401
        assert response.json()["message"] == "Invalid email or password."


class TestProtectedRoutes:
    @pytest.mark.parametrize(
        "method,path",
        [
            ("get", "/api/v1/documents"),
            ("get", "/api/v1/auth/me"),
            ("get", "/api/v1/search/debug?query=leave"),
        ],
    )
    def test_requires_token(self, auth_client, method, path):
        response = getattr(auth_client, method)(path)
        assert response.status_code == 401
        assert response.json()["error"] == "UnauthorizedError"

    def test_invalid_token_is_rejected(self, auth_client):
        response = auth_client.get("/api/v1/documents", headers=bearer("not.a.token"))
        assert response.status_code == 401

    def test_token_for_unknown_user_is_rejected(self, auth_client):
        token = create_access_token("ghost", get_settings().SECRET_KEY)
        assert auth_client.get("/api/v1/documents", headers=bearer(token)).status_code == 401

    def test_public_routes_stay_open(self, auth_client):
        assert auth_client.get("/api/v1/health").status_code == 200
        assert auth_client.get("/api/v1/auth/config").status_code == 200

    def test_users_cannot_see_each_others_documents(self, auth_client):
        rahim = register(auth_client).json()["access_token"]
        karim = register(auth_client, email="karim@example.com", name="Karim").json()["access_token"]

        upload = auth_client.post(
            "/api/v1/documents",
            files={"file": ("salary.md", b"# Salary\n\nKarim earns 90000 taka a month.", "text/markdown")},
            headers=bearer(karim),
        )
        assert upload.status_code == 202
        doc_id = upload.json()["id"]

        assert auth_client.get("/api/v1/documents", headers=bearer(karim)).json()["total"] == 1
        assert auth_client.get("/api/v1/documents", headers=bearer(rahim)).json()["total"] == 0
        assert auth_client.get(f"/api/v1/documents/{doc_id}", headers=bearer(rahim)).status_code == 404

        hits = auth_client.post(
            "/api/v1/search", json={"query": "Karim salary", "rerank": False}, headers=bearer(rahim)
        ).json()
        assert hits["results"] == []
        own = auth_client.post(
            "/api/v1/search", json={"query": "Karim salary", "rerank": False}, headers=bearer(karim)
        ).json()
        assert own["results"] and own["results"][0]["document_id"] == doc_id
