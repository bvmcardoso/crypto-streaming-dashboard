from __future__ import annotations

import os
from typing import AsyncGenerator
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./crypto.db")


class Base(DeclarativeBase):
    """Global SQLAlchemy Declarative  Base for ORM models."""

    pass


# Async engine (no autocommit/autoflush)
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Session factory (1 per request via dependency)
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Session dependency per request"""
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()
