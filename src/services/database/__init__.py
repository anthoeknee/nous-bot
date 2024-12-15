"""
Database service for the Discord bot.
Provides SQLite + SQLAlchemy implementation with session management and base models.
"""

from .base import Base, BaseModel
from .session import DatabaseSession
from .models import User
from src.core.config import config

# Create default database instance with configuration
default_db = DatabaseSession(
    session_url=config.SERVICES_CONFIG["database"]["config"]["session_url"],
    transaction_url=config.SERVICES_CONFIG["database"]["config"]["transaction_url"],
    direct_url=config.SERVICES_CONFIG["database"]["config"]["direct_url"],
    pool_size=config.SERVICES_CONFIG["database"]["config"]["pool_size"],
    pool_timeout=config.SERVICES_CONFIG["database"]["config"]["pool_timeout"],
    use_connection_pooling=config.SERVICES_CONFIG["database"]["config"][
        "use_connection_pooling"
    ],
)

# Comment out sync_tables since we're using Alembic
# default_db.sync_tables(drop_orphaned=False)

__all__ = ["Base", "BaseModel", "DatabaseSession", "User", "default_db"]
