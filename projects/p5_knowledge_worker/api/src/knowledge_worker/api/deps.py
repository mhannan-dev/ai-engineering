"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from knowledge_worker.config import Settings, get_settings
from knowledge_worker.core.exceptions import UnauthorizedError
from knowledge_worker.core.security import decode_access_token
from knowledge_worker.db.session import get_db
from knowledge_worker.services.container import Container
from knowledge_worker.services.conversation_service import ConversationService
from knowledge_worker.services.document_service import DocumentService
from knowledge_worker.services.user_service import UserService

SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[Session, Depends(get_db)]


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_user_service(db: DatabaseDep) -> UserService:
    return UserService(db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]

# auto_error=False so a missing header becomes our own 401 shape instead of FastAPI's 403.
# It also adds the "Authorize" button to Swagger.
bearer_scheme = HTTPBearer(auto_error=False, description="Token from POST /auth/login")


def get_current_user_id(
    settings: SettingsDep,
    users: UserServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    """The signed-in user's id. Every document, chunk and vector is scoped by it."""
    if not settings.AUTH_ENABLED:
        return settings.LOCAL_USER_ID
    if credentials is None:
        raise UnauthorizedError("Sign in to continue.")
    claims = decode_access_token(credentials.credentials, settings.SECRET_KEY)
    if not claims or not isinstance(claims.get("sub"), str):
        raise UnauthorizedError("Your session has expired. Sign in again.")
    # A deleted account's token must stop working even before it expires.
    if users.get(claims["sub"]) is None:
        raise UnauthorizedError("Account not found. Sign in again.")
    return claims["sub"]


CurrentUserIdDep = Annotated[str, Depends(get_current_user_id)]


def get_conversation_service(db: DatabaseDep) -> ConversationService:
    return ConversationService(db)


ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]


def get_document_service(db: DatabaseDep, container: ContainerDep) -> DocumentService:
    return DocumentService(db, container.settings, container.pipeline, container.enqueue)


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]


def get_retriever(container: ContainerDep):
    return container.retriever


RetrieverDep = Annotated[object, Depends(get_retriever)]


def get_generator(container: ContainerDep):
    return container.generator


GeneratorDep = Annotated[object, Depends(get_generator)]
