"""Database session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from src.services.base import ServiceInterface
from .base import Base

logger = logging.getLogger(__name__)


class DatabaseSession(ServiceInterface):
    """Manages database connections and sessions."""

    def __init__(
        self,
        session_url: str,
        transaction_url: str = None,
        direct_url: str = None,
        pool_size: int = 20,
        pool_timeout: int = 30,
        use_connection_pooling: bool = True,
    ):
        """Initialize database connection."""
        # Use direct URL if connection pooling is disabled
        connection_url = direct_url if not use_connection_pooling else session_url

        engine_args = {
            "pool_pre_ping": True,
            "echo": False,  # Set to True for SQL query logging
        }

        if use_connection_pooling:
            engine_args.update(
                {
                    "pool_size": pool_size,
                    "pool_timeout": pool_timeout,
                }
            )
        else:
            engine_args["poolclass"] = NullPool

        self.engine = create_async_engine(connection_url, **engine_args)
        self.SessionFactory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async context manager for database sessions.

        Usage:
            async with db.session() as session:
                user = await User.create(session, name="John")
                await session.commit()
        """
        session = self.SessionFactory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

    async def create_tables(self) -> None:
        """Create all tables defined in models."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all tables. Use with caution!"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def start(self) -> None:
        """Initialize database connection"""
        # Test connection using SQLAlchemy text construct
        async with self.engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to database")

    async def stop(self) -> None:
        """Close all connections"""
        await self.engine.dispose()
        logger.info("Database connections closed")
