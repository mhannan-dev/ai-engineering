"""Upload domain entity (any file stored by the application)."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


class UploadCategory:
    """Known upload categories; each maps to its own subfolder under UPLOAD_DIR."""

    AVATAR = "avatar"


@dataclass
class Upload:
    """Metadata for a file stored under UPLOAD_DIR."""

    user_id: str
    category: str
    stored_path: str  # relative to UPLOAD_DIR, e.g. "avatars/<id>.webp"
    content_type: str
    size_bytes: int
    original_filename: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def url(self) -> str:
        """Public URL path (files are served by the /uploads static mount)."""
        return f"/uploads/{self.stored_path}"
