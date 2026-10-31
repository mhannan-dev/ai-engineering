"""Schemas for saved chat conversations."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationPage(BaseModel):
    items: list[ConversationOut]
    total: int
    limit: int
    offset: int


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: Literal["user", "assistant"]
    content: str
    citations: list[dict[str, Any]] | None = None
    sources: list[dict[str, Any]] | None = None
    validation: dict[str, Any] | None = None
    is_abstention: bool = False
    created_at: datetime


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]
