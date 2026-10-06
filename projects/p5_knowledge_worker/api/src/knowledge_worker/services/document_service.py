"""Document upload, listing and deletion. All queries are scoped to the caller's user_id."""

import hashlib
import io
import uuid
import zipfile
from collections.abc import Callable
from pathlib import Path, PurePath

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from knowledge_worker.config import Settings
from knowledge_worker.core.exceptions import (
    ConflictError,
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileError,
)
from knowledge_worker.db.models import ChunkModel, DocumentModel
from knowledge_worker.ingestion.parsers import DocumentFormat
from knowledge_worker.ingestion.pipeline import IngestionPipeline

SUPPORTED = "PDF, DOCX, Markdown, HTML or plain text"
_TEXT_EXTENSIONS: dict[str, DocumentFormat] = {
    ".md": "md", ".markdown": "md", ".txt": "txt", ".html": "html", ".htm": "html",
}
_DOCX_MAX_UNCOMPRESSED = 200 * 1024 * 1024  # zip-bomb guard


def detect_format(filename: str, data: bytes) -> DocumentFormat:
    """Decide the format from the bytes; the extension only picks between text flavours."""
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = set(archive.namelist())
                uncompressed = sum(info.file_size for info in archive.infolist())
        except zipfile.BadZipFile as exc:
            raise UnsupportedFileError("The file looks like a ZIP archive but is damaged.") from exc
        if "word/document.xml" not in names:
            raise UnsupportedFileError(f"Only Word .docx archives are supported ({SUPPORTED}).")
        if uncompressed > _DOCX_MAX_UNCOMPRESSED:
            raise FileTooLargeError("This .docx expands to more than 200 MB and was rejected.")
        return "docx"

    extension = PurePath(filename).suffix.lower()
    if extension in _TEXT_EXTENSIONS:
        try:
            data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise UnsupportedFileError("Text files must be UTF-8 encoded.") from exc
        if b"\x00" in data:
            raise UnsupportedFileError("This file contains binary data, not text.")
        return _TEXT_EXTENSIONS[extension]
    raise UnsupportedFileError(f"Unsupported file type. Upload {SUPPORTED}.")


class DocumentService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        pipeline: IngestionPipeline,
        enqueue: Callable[[str], None],
    ):
        self._db = db
        self._settings = settings
        self._pipeline = pipeline
        self._enqueue = enqueue

    def upload(self, user_id: str, filename: str, data: bytes) -> DocumentModel:
        if len(data) > self._settings.UPLOAD_MAX_BYTES:
            limit_mb = self._settings.UPLOAD_MAX_BYTES // (1024 * 1024)
            raise FileTooLargeError(f"Files can be at most {limit_mb} MB.")
        if not data:
            raise UnsupportedFileError("The file is empty.")

        display_name = PurePath(filename or "document").name[:255] or "document"
        fmt = detect_format(display_name, data)
        digest = hashlib.sha256(data).hexdigest()
        existing = self._db.scalar(
            select(DocumentModel).where(
                DocumentModel.user_id == user_id, DocumentModel.sha256 == digest
            )
        )
        if existing:
            raise ConflictError(
                f"This file was already uploaded as '{existing.filename}'.",
                details={"document_id": existing.id},
            )

        doc_id = str(uuid.uuid4())
        # Server-generated path; the user's filename never touches the filesystem.
        stored = Path(user_id) / f"{doc_id}.{fmt}"
        target = self._settings.upload_dir / stored
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

        doc = DocumentModel(
            id=doc_id,
            user_id=user_id,
            filename=display_name,
            format=fmt,
            size_bytes=len(data),
            sha256=digest,
            stored_path=stored.as_posix(),
            status="pending",
        )
        self._db.add(doc)
        try:
            self._db.commit()
        except Exception:
            self._db.rollback()
            target.unlink(missing_ok=True)
            raise
        self._enqueue(doc.id)
        return doc

    def list_documents(self, user_id: str, limit: int, offset: int) -> tuple[list[DocumentModel], int]:
        where = DocumentModel.user_id == user_id
        total = self._db.scalar(select(func.count()).select_from(DocumentModel).where(where)) or 0
        items = self._db.scalars(
            select(DocumentModel)
            .where(where)
            .order_by(DocumentModel.created_at.desc(), DocumentModel.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return list(items), total

    def get(self, user_id: str, document_id: str) -> DocumentModel:
        doc = self._db.get(DocumentModel, document_id)
        if doc is None or doc.user_id != user_id:
            raise NotFoundError("Document not found.")  # 404 for other users' documents too
        return doc

    def list_chunks(
        self, user_id: str, document_id: str, limit: int, offset: int
    ) -> tuple[list[ChunkModel], int]:
        doc = self.get(user_id, document_id)
        where = ChunkModel.document_id == doc.id
        total = self._db.scalar(select(func.count()).select_from(ChunkModel).where(where)) or 0
        items = self._db.scalars(
            select(ChunkModel).where(where).order_by(ChunkModel.ordinal).limit(limit).offset(offset)
        ).all()
        return list(items), total

    def reindex(self, user_id: str, document_id: str) -> DocumentModel:
        doc = self.get(user_id, document_id)
        if doc.status in ("pending", "processing"):
            raise ConflictError("This document is already being indexed.")
        doc.status, doc.error_message = "pending", None
        self._db.commit()
        self._enqueue(doc.id)
        return doc

    def delete(self, user_id: str, document_id: str) -> None:
        doc = self.get(user_id, document_id)
        if doc.status == "processing":
            raise ConflictError("This document is being indexed. Delete it when indexing finishes.")
        self._pipeline.delete_vectors(user_id, doc.id)
        path = self._settings.upload_dir / doc.stored_path
        self._db.delete(doc)
        self._db.commit()
        path.unlink(missing_ok=True)
        self._pipeline.rebuild_sparse(self._db, user_id)
