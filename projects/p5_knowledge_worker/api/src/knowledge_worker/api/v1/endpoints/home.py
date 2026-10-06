"""Home and root health check endpoints."""

from fastapi import APIRouter

from knowledge_worker.api.deps import SettingsDep

router = APIRouter()

@router.get("/", summary="Root", tags=["home"])
@router.get("/health", summary="Health check", tags=["health"])
def read_root(settings: SettingsDep) -> dict[str, str]:
    """Root and health endpoint returning welcome message, status, and API metadata."""
    return {
        "status": "ok",
        "message": "Welcome to my FastAPI application!",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
    }
