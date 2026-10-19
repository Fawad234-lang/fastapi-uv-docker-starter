"""FastAPI application factory, middleware, and global error handlers."""

import logging
import re
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from project_api import __version__
from project_api.api.v1.router import api_router
from project_api.core.config import get_settings
from project_api.core.exceptions import AppError
from project_api.schemas.chat import ErrorResponse

logger = logging.getLogger(__name__)
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def _error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    body = ErrorResponse(
        error={"code": code, "message": message, "request_id": _request_id(request)}
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"X-Request-ID": _request_id(request)},
    )


def create_app() -> FastAPI:
    """Create the app; services remain injected and replaceable in tests."""
    settings = get_settings()
    application = FastAPI(
        title="Project API",
        version=settings.app_version or __version__,
        description="A learning API with messages and a Gemini-powered chat endpoint.",
    )
    application.include_router(api_router)

    @application.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        supplied = request.headers.get("X-Request-ID", "").strip()
        request_id = supplied if _REQUEST_ID_PATTERN.fullmatch(supplied) else str(uuid.uuid4())
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            # Log diagnostics server-side; never return exception details to the caller.
            logger.exception("Unhandled request error; request_id=%s", request_id)
            response = _error_response(
                request, 500, "internal_error", "An unexpected server error occurred."
            )
        response.headers["X-Request-ID"] = request_id
        return response

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(request, exc.status_code, exc.code, exc.public_message)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Keep FastAPI's familiar detail payload, and add correlation information.
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "request_id": _request_id(request)},
            headers={"X-Request-ID": _request_id(request)},
        )

    return application


app = create_app()
