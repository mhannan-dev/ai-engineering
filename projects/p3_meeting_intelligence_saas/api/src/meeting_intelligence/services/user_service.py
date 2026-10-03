"""User management business logic service."""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from meeting_intelligence.core.exceptions import AppException, NotFoundError, UnauthorizedError
from meeting_intelligence.core.security import hash_password, verify_password
from meeting_intelligence.db.session import DatabaseSession
from meeting_intelligence.models.upload import UploadCategory
from meeting_intelligence.models.user import User
from meeting_intelligence.schemas.user import UserCreate
from meeting_intelligence.services.upload_service import UploadService


class UserService:
    """Service orchestrating user registration, validation, and retrieval."""

    def __init__(self, db: DatabaseSession):
        self.db = db

    def register_user(self, payload: UserCreate) -> User:
        """Register a new user if the email does not already exist."""
        existing = self.db.users.get_by_email(payload.email)
        if existing:
            raise AppException("A user with this email address already exists.", status_code=409)

        hashed = hash_password(payload.password)
        user = User(
            email=payload.email,
            hashed_password=hashed,
            first_name=payload.first_name,
            last_name=payload.last_name,
            subscription_tier=payload.subscription_tier or "free",
        )
        return self.db.users.create(user)

    def authenticate_user(self, email: str, plain_password: str) -> User:
        """Verify user credentials and return the active user entity."""
        user = self.db.users.get_by_email(email)
        if not user or not verify_password(plain_password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedError("User account is inactive.")
        return user

    def get_by_id(self, user_id: str) -> User:
        """Retrieve user by ID or raise NotFoundError."""
        user = self.db.users.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} was not found.")
        return user

    def list_users(self) -> list[User]:
        """List all registered users."""
        return self.db.users.list_all()

    def update_user(self, user_id: str, first_name: str | None = None, last_name: str | None = None) -> User:
        """Update user profile information."""
        updated = self.db.users.update(user_id, first_name=first_name, last_name=last_name)
        if not updated:
            raise NotFoundError(f"User with ID {user_id} was not found.")
        return updated

    def update_avatar(
        self,
        user: User,
        content: bytes,
        upload_dir: Path,
        max_bytes: int,
        original_filename: str | None = None,
    ) -> User:
        """Validate, convert and store an avatar image (uploads table), replacing any previous one."""
        if not content:
            raise AppException("Uploaded image is empty.")
        if len(content) > max_bytes:
            raise AppException(
                f"Image is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.",
                status_code=413,
            )

        webp = _convert_to_webp(content)

        uploads = UploadService(self.db, upload_dir)
        previous = self.db.uploads.list_for_user(user.id, UploadCategory.AVATAR)
        # Save the new avatar before deleting old ones, so a failure never leaves the user without one
        uploads.save(
            user_id=user.id,
            category=UploadCategory.AVATAR,
            content=webp,
            extension="webp",
            content_type="image/webp",
            original_filename=original_filename,
        )
        for old in previous:
            uploads.delete(old)

        return self.get_by_id(user.id)

    def remove_avatar(self, user: User, upload_dir: Path) -> User:
        """Delete the user's avatar file(s) and their uploads records."""
        uploads = UploadService(self.db, upload_dir)
        for old in self.db.uploads.list_for_user(user.id, UploadCategory.AVATAR):
            uploads.delete(old)
        return self.get_by_id(user.id)


# Detected from file contents, not the filename/content-type
AVATAR_ALLOWED_FORMATS = ("JPEG", "PNG", "WEBP")
AVATAR_MAX_DIMENSION = 512  # px; avatars are displayed small, so downscale large photos
AVATAR_WEBP_QUALITY = 85
# Refuse images that decode to more pixels than this (decompression-bomb guard)
AVATAR_MAX_PIXELS = 40_000_000


def _convert_to_webp(content: bytes) -> bytes:
    """Decode a JPEG/PNG/WEBP image and re-encode it as a WebP avatar.

    Re-encoding also strips metadata (EXIF/GPS) and anything that isn't pixel data.
    """
    try:
        with Image.open(BytesIO(content), formats=AVATAR_ALLOWED_FORMATS) as img:
            if img.width * img.height > AVATAR_MAX_PIXELS:
                raise AppException("Image dimensions are too large.", status_code=413)

            img.seek(0)  # animated GIF/WEBP/APNG: use the first frame
            img = ImageOps.exif_transpose(img)  # honour camera rotation before EXIF is dropped
            img = img.convert("RGBA" if _has_transparency(img) else "RGB")
            img.thumbnail((AVATAR_MAX_DIMENSION, AVATAR_MAX_DIMENSION), Image.Resampling.LANCZOS)

            out = BytesIO()
            img.save(out, format="WEBP", quality=AVATAR_WEBP_QUALITY, method=6)
            return out.getvalue()
    except AppException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise AppException(
            "Unsupported or corrupted image. Only JPG, JPEG, PNG and WEBP are allowed.",
            status_code=415,
        ) from exc


def _has_transparency(img: Image.Image) -> bool:
    return img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)
