"""Database session management and repository implementations."""

from collections.abc import Generator
from dataclasses import asdict
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from meeting_intelligence.config import get_settings
from meeting_intelligence.db.base import BaseRepository
from meeting_intelligence.db.models import UserModel, MeetingModel
from meeting_intelligence.models.meeting import Meeting, ActionItemRecord, TranscriptionRecord
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
            avatar=model.avatar,
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
            avatar=item.avatar,
            subscription_tier=item.subscription_tier,
            is_active=item.is_active,
            created_at=item.created_at,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return item

    def update_avatar(self, item_id: str, avatar: str | None) -> User | None:
        model = self._db.query(UserModel).filter(UserModel.id == item_id).first()
        if not model:
            return None
        model.avatar = avatar
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

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

    def list_by_user(self, user_id: str) -> list[Meeting]:
        models = self._db.query(MeetingModel).filter(MeetingModel.user_id == user_id).order_by(MeetingModel.created_at.desc()).all()
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


class DatabaseSession:
    """Session container exposing domain repositories."""

    def __init__(self, db: Session):
        self._db = db
        self.users = UserRepository(self._db)
        self.meetings = MeetingRepository(self._db)

    @classmethod
    def reset(cls) -> None:
        """Clear all stored data (useful for test isolation)."""
        pass


def get_db() -> Generator[DatabaseSession, None, None]:
    """FastAPI dependency yielding database session."""
    db = SessionLocal()
    session = DatabaseSession(db)
    try:
        yield session
    finally:
        db.close()
