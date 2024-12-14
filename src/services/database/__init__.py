"""
Database service for the Discord bot.
Provides SQLite + SQLAlchemy implementation with session management and base models.
"""

from .base import Base, BaseModel
from .session import DatabaseSession
from .models import User

# Create default database instance
default_db = DatabaseSession()

# Sync database tables with models
default_db.sync_tables(drop_orphaned=False)

__all__ = ["Base", "BaseModel", "DatabaseSession", "User", "default_db"]
