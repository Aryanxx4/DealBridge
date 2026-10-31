"""Stable error codes and the JSON error envelope."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("dealbridge.errors")


class AppError(Exception):
    """An error with a stable code that maps to the API error envelope."""

    status_code = 400
    code = "BAD_REQUEST"

    def __init__(
        self,
        code: str | None = None,
        message: str = "",
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(message or code or self.code)
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.message = message or self.code
        self.details = details or {}
        self.headers = headers or {}


def not_found(what: str = "Resource") -> AppError:
    return AppError("NOT_FOUND", f"{what} not found.", 404)


def forbidden_role() -> AppError:
    return AppError("FORBIDDEN_ROLE", "This action is not available for your role.", 403)


def invalid_state(message: str, allowed: list[str] | None = None) -> AppError:
    return AppError("INVALID_STATE", message, 409, {"allowed_transitions": allowed or []})


class LLMNotConfigured(AppError):
    status_code = 503
    code = "LLM_NOT_CONFIGURED"

    def __init__(self):
        super().__init__(message="The language model is not configured. Set LLM_API_KEY in the backend .env.")


class LLMUnavailable(AppError):
    status_code = 503
    code = "LLM_UNAVAILABLE"

    def __init__(self, message: str = "The language model service is unavailable. Please retry."):
        super().__init__(message=message)


class LLMOutputError(AppError):
    status_code = 502
    code = "LLM_OUTPUT_INVALID"

    def __init__(self, message: str = "The language model returned output that failed validation."):
        super().__init__(message=message)


class VectorDBUnavailable(AppError):
    status_code = 503
    code = "VECTOR_DB_UNAVAILABLE"

    def __init__(self, message: str = "The vector database is unavailable. Please retry."):
        super().__init__(message=message)


class EmbeddingUnavailable(AppError):
    status_code = 503
    code = "EMBEDDING_UNAVAILABLE"

    def __init__(self, message: str = "The embedding model is unavailable."):
        super().__init__(message=message)


class ReindexRequired(AppError):
    status_code = 503
    code = "REINDEX_REQUIRED"

    def __init__(self, message: str = "The knowledge index must be rebuilt (embedding model or dimension changed)."):
        super().__init__(message=message)


INFRA_ERRORS = (LLMUnavailable, VectorDBUnavailable, EmbeddingUnavailable, LLMNotConfigured, ReindexRequired)


def envelope(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(envelope(exc.code, exc.message, exc.details), status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        errors = [
            {"loc": [str(x) for x in e.get("loc", [])], "msg": e.get("msg", ""), "type": e.get("type", "")}
            for e in exc.errors()
        ]
        return JSONResponse(envelope("VALIDATION_ERROR", "The request is invalid.", {"errors": errors}), status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 413: "PAYLOAD_TOO_LARGE"}.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(envelope(code, str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("unhandled error", extra={"route": request.url.path})
        return JSONResponse(envelope("INTERNAL_ERROR", "An unexpected error occurred."), status_code=500)
