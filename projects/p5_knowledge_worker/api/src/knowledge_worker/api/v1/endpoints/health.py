"""Health endpoint."""

from fastapi import APIRouter

from knowledge_worker.api.deps import SettingsDep
from knowledge_worker.schemas.document import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health check")
def health_check(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(status="ok", version=settings.VERSION)
