"""Test fixtures and test environment setup."""

import pytest
from fastapi.testclient import TestClient

from meeting_intelligence.config import Settings, get_settings
from meeting_intelligence.db.session import DatabaseSession
from meeting_intelligence.main import create_app


def get_test_settings() -> Settings:
    """Return test settings with fast tokens and testing environment."""
    return Settings(
        ENVIRONMENT="testing",
        SECRET_KEY="test-secret-key-meeting-intelligence-32-chars-long",
        ACCESS_TOKEN_EXPIRE_MINUTES=60,
    )


@pytest.fixture(autouse=True)
def clean_database():
    """Reset database state between tests."""
    DatabaseSession.reset()
    yield
    DatabaseSession.reset()


@pytest.fixture
def app():
    """Create a configured test application instance."""
    app_instance = create_app()
    app_instance.dependency_overrides[get_settings] = get_test_settings
    return app_instance


@pytest.fixture
def client(app):
    """Yield a synchronous TestClient instance for API integration testing."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    """Register and authenticate a default user, returning Bearer auth header."""
    client.post(
        "/api/v1/users/",
        json={"email": "alice@example.com", "password": "Password123!", "full_name": "Alice Developer"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
