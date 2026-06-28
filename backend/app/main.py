from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.database.base import Base
from app.database.session import engine
from app.models import media  # noqa: F401 — register media tables
from app.models import platform  # noqa: F401 — register platform tables
from app.routers import admin, auth, chat, developer, hospital, line, media, rag, reservation, subscription

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS job_function VARCHAR(255)"
        ))
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_photo_id UUID"
        ))
        await conn.execute(text(
            "ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS asset_id UUID"
        ))
        await conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS chat_cleared_at TIMESTAMPTZ"
        ))
    logger.info("Database initialized", app=settings.APP_NAME)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = settings.API_PREFIX
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(chat.router, prefix=API_PREFIX)
app.include_router(reservation.router, prefix=API_PREFIX)
app.include_router(hospital.router, prefix=API_PREFIX)
app.include_router(line.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(developer.router, prefix=API_PREFIX)
app.include_router(rag.router, prefix=API_PREFIX)
app.include_router(subscription.router, prefix=API_PREFIX)
app.include_router(media.router, prefix=API_PREFIX)


@app.get("/health")
async def health():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
