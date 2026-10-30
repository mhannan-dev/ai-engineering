"""Account registration and credential checks."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from knowledge_worker.core.exceptions import ConflictError, UnauthorizedError
from knowledge_worker.core.security import hash_password, verify_password
from knowledge_worker.db.models import UserModel


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def _by_email(self, email: str) -> UserModel | None:
        return self.db.scalar(select(UserModel).where(UserModel.email == email.lower()))

    def register(self, email: str, name: str, password: str) -> UserModel:
        if self._by_email(email):
            raise ConflictError("An account with this email already exists.")
        user = UserModel(
            id=str(uuid.uuid4()),
            email=email.lower(),
            name=name.strip(),
            hashed_password=hash_password(password),
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:  # two sign-ups with the same email at once
            self.db.rollback()
            raise ConflictError("An account with this email already exists.") from exc
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> UserModel:
        user = self._by_email(email)
        # Same message either way, so the response doesn't reveal which emails have accounts.
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")
        return user

    def get(self, user_id: str) -> UserModel | None:
        return self.db.get(UserModel, user_id)
