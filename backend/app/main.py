"""FastAPI application factory."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import envelope, install_error_handlers
from app.core.logging import configure_logging, register_secrets, request_id_var, user_id_var

log = logging.getLogger("dealbridge.http")

MAX_JSON_BYTES = 1024 * 1024


def _routers():
    from app.api import health, identity

    routers = [health.router, identity.router]
    # Feature routers are registered as each gate lands.
    try:
        from app.api import registry

        routers.extend(registry.ROUTERS)
    except ImportError:
        pass
    return routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.runtime import check_migrations, check_vectors, fail_interrupted_jobs, load_embedder_in_background
    from app.db.session import session_factory

    s = get_settings()
    if not app.state.skip_startup_checks:
        with session_factory()() as db:
            check_migrations(db)
            n = fail_interrupted_jobs(db)
            if n:
                log.warning("marked interrupted jobs as failed", extra={"count": n})
            check_vectors(db)
        if s.APP_ENV != "test":
            load_embedder_in_background()
    yield


def create_app(skip_startup_checks: bool = False) -> FastAPI:
    s = get_settings()  # fails fast with a readable message if settings are missing
    configure_logging(s.LOG_LEVEL)
    register_secrets(s.secret_values())

    app = FastAPI(title="DealBridge API", version="0.1.0", lifespan=lifespan, docs_url="/docs", openapi_url="/openapi.json")
    app.state.skip_startup_checks = skip_startup_checks
    install_error_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[s.FRONTEND_ORIGIN],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Demo-User-Id"],
        expose_headers=["X-Request-Id", "Content-Disposition", "Retry-After"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:16]
        request_id_var.set(rid)
        user_id_var.set("-")
        ctype = request.headers.get("content-type", "")
        clen = request.headers.get("content-length")
        if ctype.startswith("application/json") and clen and clen.isdigit() and int(clen) > MAX_JSON_BYTES:
            resp = JSONResponse(envelope("PAYLOAD_TOO_LARGE", "JSON body exceeds 1 MB."), status_code=413)
        else:
            start = time.perf_counter()
            resp = await call_next(request)
            log.info(
                "request",
                extra={
                    "route": request.url.path,
                    "method": request.method,
                    "status": resp.status_code,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 1),
                },
            )
        resp.headers["X-Request-Id"] = rid
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    for r in _routers():
        app.include_router(r, prefix="/api")
    return app


def app_factory() -> FastAPI:  # used by uvicorn --factory
    return create_app()
