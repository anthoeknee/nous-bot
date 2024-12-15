"""
Flexible caching service for the Discord bot.
Provides a Redis-based caching implementation with support for JSON and Pickle serialization.
"""

from .interface import RedisInterface
from .service import RedisService

# Create a default cache instance for general use
default_cache = RedisService(prefix="discord_bot")

__all__ = ["RedisInterface", "RedisService", "default_cache"]
