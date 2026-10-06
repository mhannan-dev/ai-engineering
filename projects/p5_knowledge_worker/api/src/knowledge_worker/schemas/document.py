"""Response schemas for documents and chunks."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

DocumentStatus = Literal["pending", "processing", "indexed", "failed"]


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    format: str
    size_bytes: int
    status: DocumentStatus
    error_message: str | None
    language: str | None
    section_count: int
    chunk_count: int
    created_at: datetime
    indexed_at: datetime | None


class DocumentPage(BaseModel):
    items: list[DocumentOut]
    total: int
    limit: int
    offset: int


class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ordinal: int
    page: int | None
    heading: str | None
    language: str
    token_count: int
    text: str


class ChunkPage(BaseModel):
    items: list[ChunkOut]
    total: int
    limit: int
    offset: int


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
