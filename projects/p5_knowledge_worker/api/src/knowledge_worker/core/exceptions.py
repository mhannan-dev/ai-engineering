"""Application exceptions and handlers. Every error response is {"error", "message", "details"}."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(message, status.HTTP_404_NOT_FOUND, details)


class ConflictError(AppException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status.HTTP_409_CONFLICT, details)


class FileTooLargeError(AppException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status.HTTP_413_CONTENT_TOO_LARGE, details)


class UnsupportedFileError(AppException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, details)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.__class__.__name__, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
            for e in exc.errors()
        ]
        first = errors[0] if errors else {"field": "", "message": "Invalid request."}
        message = f"{first['field']}: {first['message']}" if first["field"] else first["message"]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"error": "ValidationError", "message": message, "details": {"errors": errors}},
        )
