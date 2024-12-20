from typing import Any, AsyncGenerator, Dict, List, Optional, Type, TypeVar
from datetime import datetime
from contextlib import asynccontextmanager

from sqlalchemy import text, select, delete, update, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings
from src.core.exceptions import DatabaseError
from ..base import BaseService
from .interface import DatabaseInterface

T = TypeVar("T", bound=DeclarativeBase)


class DatabaseService(BaseService, DatabaseInterface[T]):
    """Enhanced database service implementation"""

    def __init__(self):
        super().__init__("database")
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None
        self._Base: Optional[Type[DeclarativeBase]] = None

    async def _initialize(self, **kwargs) -> None:
        """Initialize database engine and session maker"""
        try:
            self._engine = create_async_engine(
                str(settings.database.session_url),
                echo=settings.log_level == "DEBUG",
                pool_pre_ping=True,
                pool_size=settings.database.pool_size,
                max_overflow=10,
                pool_timeout=settings.database.pool_timeout,
                pool_recycle=3600,
                future=True,
            )

            self._sessionmaker = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )

            # Store DeclarativeBase if provided
            self._Base = kwargs.get("base_class")

        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {str(e)}") from e

    async def _start(self) -> None:
        """Verify database connection and run migrations"""
        try:
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                await self._run_migrations()
        except Exception as e:
            raise DatabaseError(f"Failed to start database service: {str(e)}") from e

    async def _stop(self) -> None:
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup"""
        if not self._sessionmaker:
            raise DatabaseError("Database service not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise DatabaseError(f"Database session error: {str(e)}") from e
        finally:
            await session.close()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic transaction management"""
        async with self.session() as session:
            async with session.begin():
                yield session

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute raw SQL query"""
        try:
            async with self.session() as session:
                result = await session.execute(text(query), params or {})
                return [dict(row) for row in result.mappings()]
        except Exception as e:
            raise DatabaseError(f"Query execution error: {str(e)}") from e

    async def get_by_id(self, model: Type[T], id: Any) -> Optional[T]:
        """Get entity by ID"""
        try:
            async with self.session() as session:
                result = await session.get(model, id)
                return result
        except Exception as e:
            raise DatabaseError(f"Failed to get entity by ID: {str(e)}") from e

    async def create(self, model: T) -> T:
        """Create new entity"""
        try:
            async with self.transaction() as session:
                session.add(model)
                await session.flush()
                await session.refresh(model)
                return model
        except Exception as e:
            raise DatabaseError(f"Failed to create entity: {str(e)}") from e

    async def update(self, model: T) -> T:
        """Update existing entity"""
        try:
            async with self.transaction() as session:
                merged_model = await session.merge(model)
                await session.flush()
                await session.refresh(merged_model)
                return merged_model
        except Exception as e:
            raise DatabaseError(f"Failed to update entity: {str(e)}") from e

    async def delete(self, model: T) -> bool:
        """Delete entity"""
        try:
            async with self.transaction() as session:
                await session.delete(model)
                return True
        except Exception as e:
            raise DatabaseError(f"Failed to delete entity: {str(e)}") from e

    async def count(self, model: Type[T], **filters) -> int:
        """Count entities with optional filters"""
        try:
            async with self.session() as session:
                query = select(func.count()).select_from(model)
                for key, value in filters.items():
                    query = query.filter(getattr(model, key) == value)
                result = await session.execute(query)
                return result.scalar() or 0
        except Exception as e:
            raise DatabaseError(f"Failed to count entities: {str(e)}") from e

    async def exists(self, model: Type[T], **filters) -> bool:
        """Check if entity exists with given filters"""
        return await self.count(model, **filters) > 0

    async def _health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            async with self._engine.begin() as conn:
                # Check basic connectivity
                await conn.execute(text("SELECT 1"))

                # Get database statistics
                result = await conn.execute(
                    text("""
                    SELECT
                        numbackends as active_connections,
                        xact_commit as transactions_committed,
                        blks_read,
                        blks_hit,
                        tup_returned,
                        tup_fetched,
                        conflicts,
                        temp_files,
                        temp_bytes,
                        deadlocks
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)
                )
                stats = result.mappings().first()

                # Get table sizes
                result = await conn.execute(
                    text("""
                    SELECT
                        relname as table_name,
                        n_live_tup as row_count,
                        pg_size_pretty(pg_total_relation_size(C.oid)) as total_size
                    FROM pg_class C
                    LEFT JOIN pg_namespace N ON (N.oid = C.relnamespace)
                    WHERE nspname NOT IN ('pg_catalog', 'information_schema')
                    AND C.relkind = 'r'
                    ORDER BY pg_total_relation_size(C.oid) DESC
                    LIMIT 5
                """)
                )
                table_stats = [dict(row) for row in result.mappings()]

                return {
                    "status": "healthy",
                    "stats": dict(stats) if stats else {},
                    "top_tables": table_stats,
                    "pool": {
                        "size": self._engine.pool.size(),
                        "checked_out": self._engine.pool.checkedin(),
                        "overflow": self._engine.pool.overflow(),
                    },
                    "last_check": datetime.now().isoformat(),
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "last_error_timestamp": datetime.now().isoformat(),
            }

    async def _run_migrations(self) -> None:
        """Run database migrations"""
        if self._Base:
            async with self._engine.begin() as conn:
                await conn.run_sync(self._Base.metadata.create_all)

    # Additional utility methods

    async def bulk_create(self, models: List[T]) -> List[T]:
        """Bulk create entities"""
        try:
            async with self.transaction() as session:
                session.add_all(models)
                await session.flush()
                for model in models:
                    await session.refresh(model)
                return models
        except Exception as e:
            raise DatabaseError(f"Failed to bulk create entities: {str(e)}") from e

    async def bulk_update(
        self, model: Type[T], values: Dict[str, Any], **filters
    ) -> int:
        """Bulk update entities matching filters"""
        try:
            async with self.transaction() as session:
                query = update(model).values(**values)
                for key, value in filters.items():
                    query = query.filter(getattr(model, key) == value)
                result = await session.execute(query)
                return result.rowcount
        except Exception as e:
            raise DatabaseError(f"Failed to bulk update entities: {str(e)}") from e

    async def bulk_delete(self, model: Type[T], **filters) -> int:
        """Bulk delete entities matching filters"""
        try:
            async with self.transaction() as session:
                query = delete(model)
                for key, value in filters.items():
                    query = query.filter(getattr(model, key) == value)
                result = await session.execute(query)
                return result.rowcount
        except Exception as e:
            raise DatabaseError(f"Failed to bulk delete entities: {str(e)}") from e
