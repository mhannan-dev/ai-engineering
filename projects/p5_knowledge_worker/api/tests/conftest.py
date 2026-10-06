"""Test setup: isolated data dir + SQLite, in-memory Qdrant, and a fast fake embedder.

Environment variables are set before the app is imported because settings and the engine are
created at import time.
"""

import hashlib
import math
import os
import tempfile
from collections.abc import Sequence
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="kw-tests-"))
os.environ["DATA_DIR"] = str(_TMP)
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["ENVIRONMENT"] = "testing"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from qdrant_client import QdrantClient  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from knowledge_worker.config import get_settings  # noqa: E402
from knowledge_worker.db.models import Base, ChunkModel, DocumentModel  # noqa: E402
from knowledge_worker.db.session import SessionLocal, engine  # noqa: E402
from knowledge_worker.ingestion.vector_store import VectorStore  # noqa: E402
from knowledge_worker.main import create_app  # noqa: E402
from knowledge_worker.services.container import Container  # noqa: E402
from knowledge_worker.text.tokenizer import tokenize  # noqa: E402

FAKE_DIM = 64


class FakeEmbedder:
    """Hashed bag-of-words vectors: deterministic, instant, and similar texts score higher."""

    dim = FAKE_DIM

    def _vector(self, text: str) -> list[float]:
        v = [0.0] * FAKE_DIM
        for token in tokenize(text):
            v[int(hashlib.md5(token.encode()).hexdigest(), 16) % FAKE_DIM] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed_passages(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    def count_tokens(self, text: str) -> int:
        return max(1, len(text.split()))


class InlineContainer(Container):
    """Runs ingestion synchronously so tests can assert on the result right away."""

    def enqueue(self, document_id: str) -> None:
        self.pipeline.run(document_id)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


@pytest.fixture
def container():
    settings = get_settings()
    vectors = VectorStore(QdrantClient(":memory:"), "test_chunks", FAKE_DIM)
    vectors.ensure_collection()
    c = InlineContainer(settings, embedder=FakeEmbedder(), vectors=vectors)
    yield c
    c.shutdown()
    with SessionLocal() as db:
        db.execute(delete(ChunkModel))
        db.execute(delete(DocumentModel))
        db.commit()


@pytest.fixture
def client(container):
    with TestClient(create_app(lambda: container)) as test_client:
        yield test_client
