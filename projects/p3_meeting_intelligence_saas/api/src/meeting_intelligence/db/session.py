"""Database session management and repository implementations."""

from collections.abc import Generator

from meeting_intelligence.db.base import BaseRepository
from meeting_intelligence.models.meeting import Meeting
from meeting_intelligence.models.user import User


class UserRepository(BaseRepository[User]):
    """Repository managing User domain persistence."""

    def __init__(self, storage: dict[str, User]):
        self._storage = storage

    def get_by_id(self, item_id: str) -> User | None:
        return self._storage.get(item_id)

    def get_by_email(self, email: str) -> User | None:
        normalized = email.lower().strip()
        for user in self._storage.values():
            if user.email.lower() == normalized:
                return user
        return None

    def list_all(self) -> list[User]:
        return list(self._storage.values())

    def create(self, item: User) -> User:
        self._storage[item.id] = item
        return item

    def delete(self, item_id: str) -> bool:
        return self._storage.pop(item_id, None) is not None


class MeetingRepository(BaseRepository[Meeting]):
    """Repository managing Meeting minutes domain persistence."""

    def __init__(self, storage: dict[str, Meeting]):
        self._storage = storage

    def get_by_id(self, item_id: str) -> Meeting | None:
        return self._storage.get(item_id)

    def list_all(self) -> list[Meeting]:
        return sorted(list(self._storage.values()), key=lambda m: m.created_at, reverse=True)

    def list_by_user(self, user_id: str) -> list[Meeting]:
        return [m for m in self.list_all() if m.user_id == user_id]

    def create(self, item: Meeting) -> Meeting:
        self._storage[item.id] = item
        return item

    def delete(self, item_id: str) -> bool:
        return self._storage.pop(item_id, None) is not None


class DatabaseSession:
    """Session container exposing domain repositories."""

    _users_storage: dict[str, User] = {}
    _meetings_storage: dict[str, Meeting] = {}

    def __init__(self) -> None:
        self.users = UserRepository(self._users_storage)
        self.meetings = MeetingRepository(self._meetings_storage)

    @classmethod
    def reset(cls) -> None:
        """Clear all stored data (useful for test isolation)."""
        cls._users_storage.clear()
        cls._meetings_storage.clear()


def get_db() -> Generator[DatabaseSession, None, None]:
    """FastAPI dependency yielding database session."""
    session = DatabaseSession()
    try:
        yield session
    finally:
        pass
