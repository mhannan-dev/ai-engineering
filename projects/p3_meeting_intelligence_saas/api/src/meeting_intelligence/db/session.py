"""Database session management and repository implementations."""

from collections.abc import Generator
from dataclasses import asdict
from datetime import datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from meeting_intelligence.config import get_settings
from meeting_intelligence.db.base import BaseRepository
from meeting_intelligence.db.models import MeetingModel, UploadModel, UserModel
from meeting_intelligence.models.meeting import ActionItemRecord, Meeting, TranscriptionRecord
from meeting_intelligence.models.upload import Upload
from meeting_intelligence.models.user import User

settings = get_settings()

# check_same_thread is SQLite-only; pool_pre_ping recovers from MySQL dropping idle connections
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=not _is_sqlite,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if _is_sqlite:
    # SQLite ignores foreign keys (e.g. uploads ON DELETE CASCADE) unless enabled per connection
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

# Schema is managed by Alembic: run `uv run alembic upgrade head`

class UserRepository(BaseRepository[User]):
    """Repository managing User domain persistence."""

    def __init__(self, db: Session):
        self._db = db

    def _to_domain(self, model: UserModel | None) -> User | None:
        if not model:
            return None
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            first_name=model.first_name,
            last_name=model.last_name,
            avatar=f"/uploads/{model.avatar_upload.stored_path}" if model.avatar_upload else None,
            subscription_tier=model.subscription_tier,
            is_active=model.is_active,
            created_at=model.created_at,
        )

    def get_by_id(self, item_id: str) -> User | None:
        model = self._db.query(UserModel).filter(UserModel.id == item_id).first()
        return self._to_domain(model)

    def get_by_email(self, email: str) -> User | None:
        model = self._db.query(UserModel).filter(UserModel.email == email.lower().strip()).first()
        return self._to_domain(model)

    def list_all(self) -> list[User]:
        models = self._db.query(UserModel).all()
        return [self._to_domain(m) for m in models]

    def create(self, item: User) -> User:
        model = UserModel(
            id=item.id,
            email=item.email.lower().strip(),
            hashed_password=item.hashed_password,
            first_name=item.first_name,
            last_name=item.last_name,
            subscription_tier=item.subscription_tier,
            is_active=item.is_active,
            created_at=item.created_at,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return item

    def update(self, item_id: str, first_name: str | None = None, last_name: str | None = None) -> User | None:
        model = self._db.query(UserModel).filter(UserModel.id == item_id).first()
        if not model:
            return None
        if first_name is not None:
            model.first_name = first_name
        if last_name is not None:
            model.last_name = last_name
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def delete(self, item_id: str) -> bool:
        model = self._db.query(UserModel).filter(UserModel.id == item_id).first()
        if model:
            self._db.delete(model)
            self._db.commit()
            return True
        return False


class MeetingRepository(BaseRepository[Meeting]):
    """Repository managing Meeting minutes domain persistence."""

    def __init__(self, db: Session):
        self._db = db

    def _to_domain(self, model: MeetingModel | None) -> Meeting | None:
        if not model:
            return None

        action_items = [ActionItemRecord(**ai) for ai in model.action_items] if model.action_items else []
        transcription = None
        if model.transcription:
            t_dict = dict(model.transcription)
            if "processed_at" in t_dict and isinstance(t_dict["processed_at"], str):
                t_dict["processed_at"] = datetime.fromisoformat(t_dict["processed_at"])
            transcription = TranscriptionRecord(**t_dict)

        return Meeting(
            id=model.id,
            title=model.title,
            date=model.date,
            executive_summary=model.executive_summary,
            key_discussion_points=model.key_discussion_points,
            decisions_made=model.decisions_made,
            action_items=action_items,
            transcription=transcription,
            user_id=model.user_id,
            created_at=model.created_at,
        )

    def get_by_id(self, item_id: str) -> Meeting | None:
        model = self._db.query(MeetingModel).filter(MeetingModel.id == item_id).first()
        return self._to_domain(model)

    def list_all(self) -> list[Meeting]:
        models = self._db.query(MeetingModel).order_by(MeetingModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def list_by_user(self, user_id: str, limit: int = 50, offset: int = 0) -> list[Meeting]:
        models = (
            self._db.query(MeetingModel)
            .filter(MeetingModel.user_id == user_id)
            .order_by(MeetingModel.created_at.desc(), MeetingModel.id)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, item: Meeting) -> Meeting:
        action_items = [asdict(ai) for ai in item.action_items] if item.action_items else []

        transcription_dict = None
        if item.transcription:
            transcription_dict = asdict(item.transcription)
            if "processed_at" in transcription_dict and transcription_dict["processed_at"]:
                transcription_dict["processed_at"] = transcription_dict["processed_at"].isoformat()

        model = MeetingModel(
            id=item.id,
            title=item.title,
            date=item.date,
            executive_summary=item.executive_summary,
            key_discussion_points=item.key_discussion_points,
            decisions_made=item.decisions_made,
            action_items=action_items,
            transcription=transcription_dict,
            user_id=item.user_id,
            created_at=item.created_at,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return item

    def delete(self, item_id: str) -> bool:
        model = self._db.query(MeetingModel).filter(MeetingModel.id == item_id).first()
        if model:
            self._db.delete(model)
            self._db.commit()
            return True
        return False


class UploadRepository(BaseRepository[Upload]):
    """Repository managing stored-file metadata (the uploads table)."""

    def __init__(self, db: Session):
        self._db = db

    def _to_domain(self, model: UploadModel | None) -> Upload | None:
        if not model:
            return None
        return Upload(
            id=model.id,
            user_id=model.user_id,
            category=model.category,
            original_filename=model.original_filename,
            stored_path=model.stored_path,
            content_type=model.content_type,
            size_bytes=model.size_bytes,
            created_at=model.created_at,
        )

    def get_by_id(self, item_id: str) -> Upload | None:
        model = self._db.query(UploadModel).filter(UploadModel.id == item_id).first()
        return self._to_domain(model)

    def list_all(self) -> list[Upload]:
        models = self._db.query(UploadModel).order_by(UploadModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def list_for_user(self, user_id: str, category: str | None = None) -> list[Upload]:
        query = self._db.query(UploadModel).filter(UploadModel.user_id == user_id)
        if category:
            query = query.filter(UploadModel.category == category)
        return [self._to_domain(m) for m in query.order_by(UploadModel.created_at.desc()).all()]

    def create(self, item: Upload) -> Upload:
        self._db.add(
            UploadModel(
                id=item.id,
                user_id=item.user_id,
                category=item.category,
                original_filename=item.original_filename,
                stored_path=item.stored_path,
                content_type=item.content_type,
                size_bytes=item.size_bytes,
                created_at=item.created_at,
            )
        )
        self._db.commit()
        return item

    def delete(self, item_id: str) -> bool:
        model = self._db.query(UploadModel).filter(UploadModel.id == item_id).first()
        if model:
            self._db.delete(model)
            self._db.commit()
            return True
        return False


class DatabaseSession:
    """Session container exposing domain repositories."""

    def __init__(self, db: Session):
        self._db = db
        self.users = UserRepository(self._db)
        self.meetings = MeetingRepository(self._db)
        self.uploads = UploadRepository(self._db)


def get_db() -> Generator[DatabaseSession, None, None]:
    """FastAPI dependency yielding database session."""
    db = SessionLocal()
    session = DatabaseSession(db)
    try:
        yield session
    finally:
        db.close()
