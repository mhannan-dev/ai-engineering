"""FastAPI application factory."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from meeting_intelligence.api.v1.endpoints import health, meetings
from meeting_intelligence.api.v1.router import api_router
from meeting_intelligence.config import get_settings
from meeting_intelligence.core.exceptions import register_exception_handlers

logger = logging.getLogger(__name__)

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
    # Turn unhandled errors into JSON 500s *inside* CORS. Otherwise Starlette's outermost
    # ServerErrorMiddleware replies without CORS headers and browsers report a NetworkError.
    @app.middleware("http")
    async def catch_unhandled_errors(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled error on %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=500,
                content={"error": "InternalServerError", "message": "Internal server error.", "details": {}},
            )

    # Added last so it is the outermost app middleware and decorates every response
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

    # Uploaded files (avatars) served as static assets
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    return app


app = create_app()
