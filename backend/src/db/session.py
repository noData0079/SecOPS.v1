# backend/src/db/session.py

from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from utils.config import Settings, settings  # type: ignore[attr-defined]
from db.models import Base


_engine: AsyncEngine | None = None
_SessionLocal: async_sessionmaker[AsyncSession] | None = None


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


def _get_database_url(cfg: Settings) -> str:
    """
    Determine the async database URL.

    Priority:
      1. DATABASE_URL_ASYNC            (env or settings)
      2. DATABASE_URL                  (converted to async if needed)
      3. fallback to in-memory sqlite+aiosqlite (for tests/dev only)
    """
    # 1. Explicit async URL
    url_async = (
        getattr(cfg, "DATABASE_URL_ASYNC", None)
        or os.getenv("DATABASE_URL_ASYNC")
    )
    if url_async:
        return url_async

    # 2. Sync-style URL (e.g. postgresql+psycopg2://) – convert to asyncpg
    url_sync = (
        getattr(cfg, "DATABASE_URL", None)
        or os.getenv("DATABASE_URL")
    )
    if url_sync:
        # basic transform: postgresql+psycopg2 -> postgresql+asyncpg
        if "+psycopg2" in url_sync:
            return url_sync.replace("+psycopg2", "+asyncpg")
        if url_sync.startswith("postgresql://"):
            return url_sync.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url_sync  # assume caller already gave an async driver

    # 3. Fallback (tests/local only)
    return "sqlite+aiosqlite:///./secops_dev.db"


# ---------------------------------------------------------------------------
# Engine / session factory
# ---------------------------------------------------------------------------


def init_engine_and_session(cfg: Settings | None = None) -> None:
    """
    Initialize the global async engine and sessionmaker.

    Called implicitly on first `get_engine()`/`get_sessionmaker()` use,
    but can also be invoked eagerly at startup.
    """
    global _engine, _SessionLocal

    if _engine is not None and _SessionLocal is not None:
        return

    cfg = cfg or settings  # type: ignore[assignment]
    db_url = _get_database_url(cfg)

    _engine = create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        future=True,
    )
    _SessionLocal = async_sessionmaker(
        _engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


def get_engine() -> AsyncEngine:
    """
    Return the global AsyncEngine, initializing it if needed.
    """
    if _engine is None:
        init_engine_and_session()
    assert _engine is not None
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """
    Return the global async_sessionmaker, initializing it if needed.
    """
    if _SessionLocal is None:
        init_engine_and_session()
    assert _SessionLocal is not None
    return _SessionLocal


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession.

    Usage in routes/services:

        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from db.session import get_db_session

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db_session)):
            ...

    """
    session_local = get_sessionmaker()
    async with session_local() as session:
        try:
            yield session
        finally:
            # Explicit close is mostly redundant with context manager,
            # but kept for clarity.
            await session.close()


# ---------------------------------------------------------------------------
# Schema helper (optional)
# ---------------------------------------------------------------------------


async def create_all() -> None:
    """
    Create all tables defined on Base.metadata.

    This is mainly for local development / tests.
    In production you should rely on Alembic migrations instead.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
