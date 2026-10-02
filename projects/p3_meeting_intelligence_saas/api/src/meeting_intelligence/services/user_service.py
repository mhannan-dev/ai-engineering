"""User management business logic service."""

from meeting_intelligence.core.exceptions import AppException, NotFoundError, UnauthorizedError
from meeting_intelligence.core.security import hash_password, verify_password
from meeting_intelligence.db.session import DatabaseSession
from meeting_intelligence.models.user import User
from meeting_intelligence.schemas.user import UserCreate


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
            full_name=payload.full_name or "",
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
