"""Health and diagnostic endpoints."""

from fastapi import APIRouter

from meeting_intelligence.api.deps import SettingsDep
from meeting_intelligence.schemas.health import EchoRequest, EchoResponse, HealthResponse

router = APIRouter()


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Health check (Root)",
    description="Return service health status and the deployed API version at the root path.",
)
@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Return service health status and the deployed API version.",
)
async def health_check(settings: SettingsDep) -> HealthResponse:
    """Check service availability."""
    return HealthResponse(status="ok", version=settings.VERSION)


@router.post(
    "/echo",
    response_model=EchoResponse,
    summary="Echo a message",
    description="Echo back the message along with its length for verification.",
)
async def echo(payload: EchoRequest) -> EchoResponse:
    """Echo endpoint for connectivity diagnostics."""
    return EchoResponse(you_said=payload.message, length=len(payload.message))
