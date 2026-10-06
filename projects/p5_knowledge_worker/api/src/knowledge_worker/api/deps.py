"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from knowledge_worker.config import Settings, get_settings
from knowledge_worker.db.session import get_db
from knowledge_worker.services.container import Container
from knowledge_worker.services.document_service import DocumentService

SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[Session, Depends(get_db)]


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def get_current_user_id(settings: SettingsDep) -> str:
    """Single local user until Phase 6 replaces this with JWT auth (as in P3)."""
    return settings.LOCAL_USER_ID


CurrentUserIdDep = Annotated[str, Depends(get_current_user_id)]


def get_document_service(db: DatabaseDep, container: ContainerDep) -> DocumentService:
    return DocumentService(db, container.settings, container.pipeline, container.enqueue)


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
