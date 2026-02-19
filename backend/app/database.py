"""Async SQLAlchemy database setup with SQLite."""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        from app.models.db_models import WatchlistItem, CachedNewsItem, Evaluation, Cohort, CohortMember  # noqa
        await conn.run_sync(Base.metadata.create_all)

    # Migrations: add columns that create_all won't add to existing tables
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE evaluations ADD COLUMN score_factors TEXT"))
            logger.info("Migration: added score_factors column to evaluations")
        except Exception:
            pass  # Column already exists
