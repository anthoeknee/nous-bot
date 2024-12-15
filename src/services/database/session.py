"""Database session management."""

from contextlib import contextmanager
from typing import Generator, Set
import logging
from sqlalchemy import MetaData, Table, create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import sys

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
        """
        Initialize database connection.

        Args:
            session_url: Main database URL for regular queries
            transaction_url: URL for transaction-heavy operations
            direct_url: Direct connection URL bypassing pooler
            pool_size: Maximum number of connections in pool
            pool_timeout: Seconds to wait for available connection
            use_connection_pooling: Whether to use connection pooling
        """
        # Use direct URL if connection pooling is disabled
        connection_url = direct_url if not use_connection_pooling else session_url

        # Replace asyncpg with psycopg2 for Alembic compatibility
        if "alembic" in sys.modules:
            connection_url = connection_url.replace("postgresql+asyncpg", "postgresql")
            engine_args = {
                "pool_pre_ping": True,
                "poolclass": NullPool,
            }
        else:
            engine_args = {
                "pool_pre_ping": True,
                "pool_size": pool_size if use_connection_pooling else None,
                "pool_timeout": pool_timeout if use_connection_pooling else None,
                "poolclass": None if use_connection_pooling else NullPool,
            }

        self.engine = create_engine(connection_url, **engine_args)

        # Initialize inspector
        self._inspector = inspect(self.engine)

        self.SessionFactory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,  # Better performance for our use case
        )

    def _get_existing_tables(self) -> Set[str]:
        """Get set of existing table names in the database."""
        return set(self._inspector.get_table_names())

    def _get_model_tables(self) -> Set[str]:
        """Get set of table names defined in models."""
        return set(Base.metadata.tables.keys())

    def sync_tables(self, drop_orphaned: bool = False) -> None:
        """
        Synchronize database tables with model definitions.
        In production, you should use Alembic migrations instead.
        """
        existing_tables = self._get_existing_tables()
        model_tables = self._get_model_tables()

        # Tables to create (in models but not in database)
        tables_to_create = model_tables - existing_tables
        if tables_to_create:
            logger.info(f"Creating new tables: {tables_to_create}")
            # Create only the new tables
            for table_name in tables_to_create:
                if table_name in Base.metadata.tables:
                    Base.metadata.tables[table_name].create(self.engine)

        # Tables to drop (in database but not in models)
        orphaned_tables = existing_tables - model_tables
        if orphaned_tables:
            if drop_orphaned:
                logger.warning(f"Dropping orphaned tables: {orphaned_tables}")
                # Drop orphaned tables
                for table_name in orphaned_tables:
                    Table(table_name, MetaData()).drop(self.engine)
            else:
                logger.warning(
                    f"Found orphaned tables (not dropping): {orphaned_tables}"
                )

    def create_tables(self) -> None:
        """Create all tables defined in models."""
        Base.metadata.create_all(self.engine)

    def drop_tables(self) -> None:
        """Drop all tables. Use with caution!"""
        Base.metadata.drop_all(self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Usage:
            with db.session() as session:
                user = User.create(session, name="John")
                session.commit()
        """
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_session(self) -> Session:
        """Get a new session. Remember to close it when done!"""
        return self.SessionFactory()

    async def start(self) -> None:
        """Initialize connection pool and verify database connection"""
        try:
            # Test connection
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("Successfully connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    async def stop(self) -> None:
        """Close all connections"""
        self.engine.dispose()
        logger.info("Database connections closed")
