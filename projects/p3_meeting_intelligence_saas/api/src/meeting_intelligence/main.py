"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from meeting_intelligence.api.v1.endpoints import health, meetings
from meeting_intelligence.api.v1.router import api_router
from meeting_intelligence.config import get_settings
from meeting_intelligence.core.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    """Initialize and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Backend for the Hybrid Audio Meeting Minutes & Action Items Engine.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    register_exception_handlers(app)

    # Mount API routers
    app.include_router(api_router, prefix=settings.API_V1_STR)
    # Direct top-level health routes
    app.include_router(health.router)
    # Direct process-audio route for Next.js client compatibility
    app.add_api_route(
        "/api/process-audio",
        meetings.process_audio,
        methods=["POST"],
        response_model=meetings.MeetingMinutesSchema,
        tags=["meetings"],
        summary="Process audio upload",
    )

    return app


app = create_app()
