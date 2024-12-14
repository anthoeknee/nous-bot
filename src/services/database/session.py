"""Database session management."""

from contextlib import contextmanager
from typing import Generator, Set
import logging
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import Table

from .base import Base, ServiceInterface

logger = logging.getLogger(__name__)


class DatabaseSession(ServiceInterface):
    """Manages database connections and sessions."""

    def __init__(self, database_url: str = "sqlite:///bot.db"):
        """
        Initialize database connection.

        Args:
            database_url: SQLAlchemy database URL. Defaults to SQLite.
        """
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},  # Required for SQLite
            poolclass=StaticPool,  # Better for single-threaded applications
        )
        self.SessionFactory = sessionmaker(bind=self.engine)
        self._inspector = inspect(self.engine)

    def _get_existing_tables(self) -> Set[str]:
        """Get set of existing table names in the database."""
        return set(self._inspector.get_table_names())

    def _get_model_tables(self) -> Set[str]:
        """Get set of table names defined in models."""
        return set(Base.metadata.tables.keys())

    def sync_tables(self, drop_orphaned: bool = False) -> None:
        """
        Synchronize database tables with model definitions.

        Args:
            drop_orphaned: If True, drops tables that exist in database but not in models.
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
        # Initialize connection pool and create tables
        self.create_tables()

    async def stop(self) -> None:
        # Close all sessions and connection pool
        self.engine.dispose()
