import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth.router import router as auth_router
from app.api.chat.router import router as chat_router
from app.api.documents.router import router as documents_router
from app.config import get_settings
from app.db.client import close_client, get_database
from app.db.indexes import ensure_indexes
from app.utils.errors import AppError

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_database()
    try:
        await ensure_indexes(db)
        logger.info("Database indexes ensured")
    except Exception as exc:
        logger.warning("Could not ensure indexes: %s", exc)
    yield
    await close_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Self-Healing RAG Assistant", version="1.0.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def generic_error_handler(_: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(chat_router, prefix="/chat", tags=["chat"])
    app.include_router(documents_router, prefix="/documents", tags=["documents"])

    return app


app = create_app()
