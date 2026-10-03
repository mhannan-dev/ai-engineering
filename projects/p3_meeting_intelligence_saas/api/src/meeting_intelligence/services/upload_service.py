"""Generic file storage: writes files under UPLOAD_DIR and records them in the uploads table."""

import uuid
from pathlib import Path

from meeting_intelligence.db.session import DatabaseSession
from meeting_intelligence.models.upload import Upload


class UploadService:
    """Stores and deletes application files, keeping disk and the uploads table in sync."""

    def __init__(self, db: DatabaseSession, upload_dir: Path):
        self.db = db
        self.upload_dir = upload_dir

    def save(
        self,
        *,
        user_id: str,
        category: str,
        content: bytes,
        extension: str,
        content_type: str,
        original_filename: str | None = None,
    ) -> Upload:
        """Write `content` to <UPLOAD_DIR>/<category>s/<uuid>.<ext> and record it."""
        upload_id = str(uuid.uuid4())
        # Server-generated path only; never derived from the client's filename
        stored_path = f"{category}s/{upload_id}.{extension.lstrip('.').lower()}"
        path = self.upload_dir / stored_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

        upload = Upload(
            id=upload_id,
            user_id=user_id,
            category=category,
            original_filename=(Path(original_filename).name[:255] if original_filename else None),
            stored_path=stored_path,
            content_type=content_type,
            size_bytes=len(content),
        )
        try:
            return self.db.uploads.create(upload)
        except Exception:
            path.unlink(missing_ok=True)  # don't leave orphaned files behind
            raise

    def delete(self, upload: Upload) -> None:
        """Remove the file from disk and its record from the uploads table."""
        self._resolve(upload.stored_path).unlink(missing_ok=True)
        self.db.uploads.delete(upload.id)

    def _resolve(self, stored_path: str) -> Path:
        """Absolute path for a stored file, refusing anything outside UPLOAD_DIR."""
        root = self.upload_dir.resolve()
        path = (root / stored_path).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"Refusing to touch file outside upload dir: {stored_path}")
        return path
