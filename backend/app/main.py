import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.core.observability import init_sentry
from app.core.errors import install_error_handlers
from app.core.logging import setup_logging
from app.core.redis import get_redis
from app.db.session import dispose_engine, get_engine
from app.modules.admin.router import router as admin_router
from app.modules.contact.router import router as contact_router
from app.modules.assistant.router import router as assistant_router
from app.modules.auth.router import router as auth_router
from app.modules.billing.router import pricing_router
from app.modules.billing.router import router as tariffs_router
from app.modules.catalog.router import router as catalog_router
from app.modules.files.router import router as files_router
from app.modules.meta.router import router as meta_router
from app.modules.payments.click import router as click_router
from app.modules.payments.payme import router as payme_router
from app.modules.payments.router import router as payments_router
from app.modules.plans.router import router as plans_router
from app.modules.telegram.router import router as telegram_router
from app.modules.users.router import router as me_router

log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    s = get_settings()
    setup_logging(s.log_level)
    init_sentry("api")
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title=s.app_name, version="1.0.0", lifespan=lifespan,
                  docs_url=None if s.is_production else "/docs", redoc_url=None)
    install_error_handlers(app)
    app.add_middleware(CORSMiddleware, allow_origins=s.origins, allow_credentials=True,
                       allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
                       allow_headers=["Authorization", "Content-Type", "X-Request-ID"], max_age=600)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        start = time.perf_counter()
        response = await call_next(request)
        ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if s.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if request.url.path not in ("/healthz", "/readyz"):
            log.info("request", extra={"request_id": rid, "path": request.url.path,
                                       "status": response.status_code, "duration_ms": ms})
        return response

    for r in (auth_router, me_router, tariffs_router, pricing_router, plans_router, catalog_router, payments_router,
              click_router, payme_router, admin_router, meta_router, telegram_router, files_router, contact_router, assistant_router):
        app.include_router(r)

    @app.get("/healthz", include_in_schema=False)
    async def healthz():
        return {"status": "ok"}

    @app.get("/readyz", include_in_schema=False)
    async def readyz():
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        await get_redis().ping()
        return {"status": "ready"}

    return app


app = create_app()
