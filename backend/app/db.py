from pathlib import Path
from typing import AsyncGenerator

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

logger = structlog.get_logger(__name__)

SCHEMA_SQL_PATH = Path(__file__).parent / "schema.sql"

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        engine = get_engine()
        _sessionmaker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


async def apply_schema(engine: AsyncEngine) -> None:
    """Executes schema.sql statements idempotently."""
    logger.info("db_apply_schema_start")
    sql_text = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    
    # Split queries on semicolon while ignoring empty statements
    statements = [stmt.strip() for stmt in sql_text.split(";") if stmt.strip()]

    async with engine.begin() as conn:
        for stmt in statements:
            await conn.execute(text(stmt))
    logger.info("db_apply_schema_success", statements_count=len(statements))


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an AsyncSession with automatic transaction rollback on error."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
