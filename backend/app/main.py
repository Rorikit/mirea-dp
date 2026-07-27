import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.operator import router as operator_router
from app.api.v1.public import router as public_router
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.db import async_session_factory
from app.exceptions import AppError
from app.settings import settings

logger = logging.getLogger(__name__)


def _error(
    request: Request,
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": str(getattr(request.state, "request_id", "unknown")),
            }
        },
    )


def create_app() -> FastAPI:
    configure_logging()
    application = FastAPI(title=settings.app_name, version="1.0.0")
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            "X-CSRF-Token",
            "X-Request-ID",
        ],
    )

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _error(request, exc.code, exc.message, exc.status_code, exc.details)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = {
            "fields": [
                {"path": ".".join(str(part) for part in error["loc"]), "type": error["type"]}
                for error in exc.errors()
            ]
        }
        return _error(request, "VALIDATION_ERROR", "Проверьте введённые данные", 422, details)

    @application.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Необработанная ошибка",
            extra={"request_id": str(getattr(request.state, "request_id", "unknown"))},
        )
        return _error(request, "INTERNAL_ERROR", "Внутренняя ошибка сервера", 500)

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/ready", tags=["system"])
    async def ready() -> dict[str, str]:
        try:
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1"))
        except Exception as exc:
            raise AppError("NOT_READY", "База данных недоступна", 503) from exc
        return {"status": "ready"}

    for router in (public_router, auth_router, operator_router, admin_router):
        application.include_router(router, prefix="/api/v1")
    return application


app = create_app()
