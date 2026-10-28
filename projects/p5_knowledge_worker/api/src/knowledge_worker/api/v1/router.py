"""Aggregated v1 router."""

from fastapi import APIRouter

from knowledge_worker.api.v1.endpoints import chat, documents, health, search

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
