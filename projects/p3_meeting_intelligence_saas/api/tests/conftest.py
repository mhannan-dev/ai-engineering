"""Test fixtures and test environment setup."""

import os
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

# Isolate tests from the real database and uploads BEFORE the app is imported:
# the SQLAlchemy engine is created at import time from DATABASE_URL. Environment
# variables take precedence over api/.env, so tests never touch MySQL or api/uploads.
_TEST_ROOT = Path(tempfile.mkdtemp(prefix="meeting_intel_tests_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_ROOT / 'test.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(_TEST_ROOT / "uploads")
os.environ["ENVIRONMENT"] = "testing"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from meeting_intelligence.config import Settings, get_settings  # noqa: E402
from meeting_intelligence.db.models import Base  # noqa: E402
from meeting_intelligence.db.session import DatabaseSession, SessionLocal, engine  # noqa: E402
from meeting_intelligence.main import create_app  # noqa: E402

assert engine.url.get_backend_name() == "sqlite", "Refusing to run tests against a non-test database"


def get_test_settings() -> Settings:
    """Return test settings with fast tokens and testing environment."""
    return Settings(
        ENVIRONMENT="testing",
        SECRET_KEY="test-secret-key-meeting-intelligence-32-chars-long",
        ACCESS_TOKEN_EXPIRE_MINUTES=60,
    )


@pytest.fixture(autouse=True)
def clean_database():
    """Give every test empty tables and an empty upload directory."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    shutil.rmtree(os.environ["UPLOAD_DIR"], ignore_errors=True)
    yield


class _FakeWhisperModel:
    """Stand-in for faster_whisper.WhisperModel: no model download, no audio decoding."""

    def __init__(self, *args, **kwargs):
        pass

    def transcribe(self, audio, **kwargs):
        segments = [SimpleNamespace(text="Hello team."), SimpleNamespace(text="Ship it Friday.")]
        return iter(segments), SimpleNamespace(duration=12.5)


@pytest.fixture(autouse=True)
def fake_whisper(monkeypatch):
    """Keep tests fast and deterministic: never load or run the real speech model."""
    import faster_whisper

    monkeypatch.setattr(faster_whisper, "WhisperModel", _FakeWhisperModel)


@pytest.fixture
def db_session():
    """Repository container bound to the test database."""
    db = SessionLocal()
    try:
        yield DatabaseSession(db)
    finally:
        db.close()


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


def register_and_login(client: TestClient, email: str, first_name: str = "Test") -> dict[str, str]:
    """Create a user and return its Bearer auth header."""
    client.post(
        "/api/v1/users/",
        json={"email": email, "password": "Password123!", "first_name": first_name},
    )
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}


@pytest.fixture
def make_user(client):
    """Factory fixture: make_user(email, first_name) -> Bearer auth header for a new user."""
    return lambda email, first_name="Test": register_and_login(client, email, first_name)


@pytest.fixture
def auth_headers(make_user):
    """Register and authenticate a default user, returning Bearer auth header."""
    return make_user("alice@example.com", "Alice")


def pytest_sessionfinish(session, exitstatus):
    """Remove the temporary database and uploads after the run."""
    engine.dispose()
    shutil.rmtree(_TEST_ROOT, ignore_errors=True)
