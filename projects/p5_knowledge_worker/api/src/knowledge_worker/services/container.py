"""Process-wide singletons: embedding model, Qdrant client, BM25 index and the ingestion worker.

The worker is a single thread on purpose: embedding is CPU-bound, the model is large, and
embedded Qdrant is not safe for concurrent writers.
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select

from knowledge_worker.config import Settings
from knowledge_worker.db.models import DocumentModel
from knowledge_worker.db.session import SessionLocal
from knowledge_worker.ingestion.embedder import Embedder, FastEmbedEmbedder
from knowledge_worker.ingestion.pipeline import IngestionPipeline
from knowledge_worker.ingestion.sparse_index import SparseIndex
from knowledge_worker.ingestion.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Container:
    def __init__(self, settings: Settings, embedder: Embedder | None = None,
                 vectors: VectorStore | None = None):
        self.settings = settings
        self.embedder = embedder or FastEmbedEmbedder(
            settings.EMBEDDING_MODEL,
            cache_dir=str(settings.model_cache_dir),
            dim=settings.EMBEDDING_DIM,
            query_prefix=settings.EMBEDDING_QUERY_PREFIX,
            passage_prefix=settings.EMBEDDING_PASSAGE_PREFIX,
        )
        self.vectors = vectors or VectorStore.connect(
            settings.QDRANT_URL, str(settings.qdrant_path), settings.QDRANT_COLLECTION,
            settings.EMBEDDING_DIM,
        )
        self.sparse = SparseIndex(settings.bm25_dir)
        self.pipeline = IngestionPipeline(
            settings, SessionLocal, self.embedder, self.vectors, self.sparse
        )
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ingest")
        self._busy = threading.Event()

    def enqueue(self, document_id: str) -> None:
        self._worker.submit(self._run, document_id)

    def _run(self, document_id: str) -> None:
        self._busy.set()
        try:
            self.pipeline.run(document_id)
        except Exception:
            logger.exception("Ingestion worker crashed on document %s", document_id)
        finally:
            self._busy.clear()

    def resume_unfinished(self) -> int:
        """Re-queue documents left pending/processing by a previous run that was stopped."""
        with SessionLocal() as db:
            ids = db.scalars(
                select(DocumentModel.id)
                .where(DocumentModel.status.in_(("pending", "processing")))
                .order_by(DocumentModel.created_at)
            ).all()
        for document_id in ids:
            self.enqueue(document_id)
        return len(ids)

    def shutdown(self) -> None:
        # Don't block Ctrl+C on a long PDF. Queued and interrupted documents stay
        # pending/processing and are re-queued by resume_unfinished() on the next start.
        self._worker.shutdown(wait=False, cancel_futures=True)
        if not self._busy.is_set():
            self.vectors.close()
