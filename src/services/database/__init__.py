"""
Database service for the Discord bot.
Provides SQLite + SQLAlchemy implementation with session management and base models.
"""

from .base import Base, BaseModel
from .session import DatabaseSession
from .models import User
from src.core.config import config

# Create default database instance with configuration from config
default_db = DatabaseSession(
    session_url=config.DATABASE_URLS["session"],
    transaction_url=config.DATABASE_URLS["transaction"],
    direct_url=config.DATABASE_URLS["direct"],
)

# Comment out sync_tables since we're using Alembic
# default_db.sync_tables(drop_orphaned=False)

__all__ = ["Base", "BaseModel", "DatabaseSession", "User", "default_db"]
