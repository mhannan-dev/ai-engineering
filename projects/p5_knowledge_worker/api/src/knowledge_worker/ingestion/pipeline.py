"""Index one document: parse -> chunk -> embed -> Qdrant + chunks table -> rebuild BM25.

Runs on a single background worker thread (see services/container.py), so documents are
indexed one at a time and the embedding model is never loaded twice.
"""

import logging
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from knowledge_worker.config import Settings
from knowledge_worker.db.models import ChunkModel, DocumentModel
from knowledge_worker.ingestion.chunker import chunk_sections
from knowledge_worker.ingestion.embedder import Embedder
from knowledge_worker.ingestion.parsers import ParseError, parse_document
from knowledge_worker.ingestion.sparse_index import SparseIndex
from knowledge_worker.ingestion.vector_store import VectorPoint, VectorStore
from knowledge_worker.text.language import detect_language, looks_like_bijoy

logger = logging.getLogger(__name__)

BIJOY_MESSAGE = (
    "This file uses a legacy Bangla font encoding (Bijoy / SutonnyMJ), so its text extracts as "
    "Latin gibberish. Convert it to Unicode Bangla (e.g. with Avro's converter) and upload again."
)


def document_language(chunk_languages: list[tuple[str, int]]) -> str:
    """Token-weighted language of a document: 'mixed' unless one language has >= 80%."""
    weights: Counter[str] = Counter()
    for language, tokens in chunk_languages:
        if language == "mixed":
            weights["en"] += tokens / 2
            weights["bn"] += tokens / 2
        elif language != "unknown":
            weights[language] += tokens
    total = sum(weights.values())
    if not total:
        return "unknown"
    language, top = weights.most_common(1)[0]
    return language if top / total >= 0.8 else "mixed"


class IngestionPipeline:
    def __init__(
        self,
        settings: Settings,
        session_factory: sessionmaker[Session],
        embedder: Embedder,
        vectors: VectorStore,
        sparse: SparseIndex,
    ):
        self._settings = settings
        self._sessions = session_factory
        self._embedder = embedder
        self._vectors = vectors
        self._sparse = sparse

    def run(self, document_id: str) -> None:
        with self._sessions() as db:
            doc = db.get(DocumentModel, document_id)
            if doc is None:
                return  # deleted before the worker got to it
            doc.status, doc.error_message = "processing", None
            db.commit()
            try:
                self._index(db, doc)
            except Exception as exc:
                db.rollback()
                if isinstance(exc, ParseError):
                    message = str(exc)
                else:
                    logger.exception("Indexing failed for document %s", document_id)
                    message = "Indexing failed because of an internal error. Try re-indexing."
                self._mark_failed(db, document_id, message)

    def _index(self, db: Session, doc: DocumentModel) -> None:
        data = (self._settings.upload_dir / Path(doc.stored_path)).read_bytes()
        sections = parse_document(data, doc.format)  # type: ignore[arg-type]
        if looks_like_bijoy("\n".join(s.text for s in sections[:20])):
            raise ParseError(BIJOY_MESSAGE)

        chunks = chunk_sections(
            sections,
            max_tokens=self._settings.CHUNK_MAX_TOKENS,
            overlap_tokens=self._settings.CHUNK_OVERLAP_TOKENS,
            count=self._embedder.count_tokens,
        )
        # The heading is part of what the passage is about, so it is embedded with the text.
        vectors = self._embedder.embed_passages(
            [f"{c.heading}\n{c.text}" if c.heading else c.text for c in chunks]
        )

        # Re-indexing replaces the previous chunks.
        self._vectors.delete_document(doc.user_id, doc.id)
        db.execute(delete(ChunkModel).where(ChunkModel.document_id == doc.id))

        rows = [
            ChunkModel(
                id=str(uuid.uuid4()),
                document_id=doc.id,
                user_id=doc.user_id,
                ordinal=i,
                page=c.page,
                heading=c.heading[:500] if c.heading else None,
                language=detect_language(c.text),
                token_count=c.token_count,
                text=c.text,
            )
            for i, c in enumerate(chunks)
        ]
        db.add_all(rows)
        self._vectors.upsert(
            [VectorPoint(r.id, doc.id, doc.user_id, v) for r, v in zip(rows, vectors, strict=True)]
        )

        doc.status = "indexed"
        doc.language = document_language([(r.language, r.token_count) for r in rows])
        doc.section_count = len(sections)
        doc.chunk_count = len(rows)
        doc.indexed_at = datetime.now(UTC)
        db.commit()
        self.rebuild_sparse(db, doc.user_id)

    def _mark_failed(self, db: Session, document_id: str, message: str) -> None:
        doc = db.get(DocumentModel, document_id)
        if doc is None:
            return
        try:
            self._vectors.delete_document(doc.user_id, doc.id)
        except Exception:
            logger.exception("Could not remove vectors of failed document %s", document_id)
        db.execute(delete(ChunkModel).where(ChunkModel.document_id == document_id))
        doc.status, doc.error_message = "failed", message[:1000]
        doc.chunk_count = 0
        db.commit()
        self.rebuild_sparse(db, doc.user_id)

    def delete_vectors(self, user_id: str, document_id: str) -> None:
        self._vectors.delete_document(user_id, document_id)

    def rebuild_sparse(self, db: Session, user_id: str) -> None:
        rows = db.execute(
            select(ChunkModel.id, ChunkModel.heading, ChunkModel.text)
            .join(DocumentModel)
            .where(ChunkModel.user_id == user_id, DocumentModel.status == "indexed")
            .order_by(ChunkModel.document_id, ChunkModel.ordinal)
        ).all()
        self._sparse.rebuild(
            user_id, [(cid, f"{heading}\n{text}" if heading else text) for cid, heading, text in rows]
        )
