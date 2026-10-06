"""Aggregated v1 router."""

from fastapi import APIRouter

from knowledge_worker.api.v1.endpoints import documents, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
