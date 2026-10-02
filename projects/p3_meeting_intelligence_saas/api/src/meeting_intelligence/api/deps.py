"""Shared FastAPI dependencies for authentication, database, settings, and services."""

from typing import Annotated

from fastapi import Depends, Header

from meeting_intelligence.config import Settings, get_settings
from meeting_intelligence.core.exceptions import UnauthorizedError
from meeting_intelligence.core.security import decode_access_token
from meeting_intelligence.db.session import DatabaseSession, get_db
from meeting_intelligence.models.user import User
from meeting_intelligence.services.synthesis_service import SynthesisService
from meeting_intelligence.services.transcription_service import TranscriptionService
from meeting_intelligence.services.user_service import UserService

SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[DatabaseSession, Depends(get_db)]


def get_user_service(db: DatabaseDep) -> UserService:
    """Dependency provider for UserService."""
    return UserService(db)


def get_transcription_service(settings: SettingsDep) -> TranscriptionService:
    """Dependency provider for TranscriptionService."""
    return TranscriptionService(settings)


def get_synthesis_service(settings: SettingsDep) -> SynthesisService:
    """Dependency provider for SynthesisService."""
    return SynthesisService(settings)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
TranscriptionServiceDep = Annotated[TranscriptionService, Depends(get_transcription_service)]
SynthesisServiceDep = Annotated[SynthesisService, Depends(get_synthesis_service)]


def get_current_user(
    db: DatabaseDep,
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Extract and validate the active user from the Authorization bearer token header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header.")

    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token, settings.SECRET_KEY)
    if not payload or "sub" not in payload:
        raise UnauthorizedError("Token is invalid or expired.")

    user = db.users.get_by_id(payload["sub"])
    if not user:
        raise UnauthorizedError("User does not exist.")
    if not user.is_active:
        raise UnauthorizedError("User account is inactive.")

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
