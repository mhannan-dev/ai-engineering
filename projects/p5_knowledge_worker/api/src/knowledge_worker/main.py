"""FastAPI application factory."""

import logging
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from knowledge_worker.api.v1.endpoints import home
from knowledge_worker.api.v1.router import api_router
from knowledge_worker.config import get_settings
from knowledge_worker.core.exceptions import register_exception_handlers
from knowledge_worker.core.route_printer import print_api_routes
from knowledge_worker.services.container import Container

logger = logging.getLogger(__name__)

def create_app(container_factory: Callable[[], Container] | None = None) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        container = container_factory() if container_factory else Container(settings)
        app.state.container = container
        resumed = container.resume_unfinished()
        if resumed:
            logger.info("Re-queued %d unfinished document(s)", resumed)
        # Print the route table at startup in local/dev only, to keep production logs clean.
        if settings.is_local:
            print_api_routes(app)
        yield
        container.shutdown()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Hybrid-search RAG over your own English and Bangla documents.",
        lifespan=lifespan,
    )

    # Turn unhandled errors into JSON 500s inside CORS, so browsers see the response.
    @app.middleware("http")
    async def catch_unhandled_errors(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled error on %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=500,
                content={"error": "InternalServerError", "message": "Internal server error.",
                         "details": {}},
            )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    # Versioned API: every route in api_router is served under /api/v1.
    app.include_router(api_router, prefix=settings.API_V1_STR)
    # Root and health endpoint: confirms the API is up, healthy, and points to the docs.
    app.include_router(home.router)
    return app

app = create_app()
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("knowledge_worker.main:app", host="127.0.0.1", port=8000, reload=True)
