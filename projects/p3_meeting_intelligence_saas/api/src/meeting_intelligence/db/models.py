"""SQLAlchemy database models mapping to domain entities."""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, and_
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    subscription_tier: Mapped[str] = mapped_column(String(32), default="free")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # The user's current avatar lives in the uploads table (category="avatar")
    avatar_upload: Mapped[Optional["UploadModel"]] = relationship(
        primaryjoin=lambda: and_(
            UserModel.id == UploadModel.user_id, UploadModel.category == "avatar"
        ),
        uselist=False,
        viewonly=True,
        lazy="selectin",
    )

class UploadModel(Base):
    """Any file stored by the application (avatars, audio, documents, ...)."""

    __tablename__ = "uploads"
    __table_args__ = (Index("ix_uploads_user_id_category", "user_id", "category"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Relative to UPLOAD_DIR; the public URL is /uploads/<stored_path>
    stored_path: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    content_type: Mapped[str] = mapped_column(String(127), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

class MeetingModel(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    date: Mapped[str] = mapped_column(String(64))
    executive_summary: Mapped[str] = mapped_column(Text)  # MySQL TEXT caps at 64KB
    key_discussion_points: Mapped[list] = mapped_column(JSON, default=list)
    decisions_made: Mapped[list] = mapped_column(JSON, default=list)
    action_items: Mapped[list] = mapped_column(JSON, default=list)
    transcription: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
