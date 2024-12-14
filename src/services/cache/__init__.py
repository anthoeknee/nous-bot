"""
Flexible caching service for the Discord bot.
Provides a Redis-based caching implementation with support for JSON and Pickle serialization.
"""

from .interface import CacheInterface
from .redis import RedisCache

# Create a default cache instance for general use
default_cache = RedisCache(prefix="discord_bot")

__all__ = ["CacheInterface", "RedisCache", "default_cache"]
