from typing import Optional, Union, TypeVar, Callable, Any
import json
import pickle
import redis
import asyncio

from src.services.base import ServiceInterface
from .interface import RedisInterface
from src.utils.logging import get_logger

T = TypeVar("T")
logger = get_logger()


class RedisService(ServiceInterface, RedisInterface):
    """Redis-based cache implementation with flexible serialization."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str = None,
        prefix: str = "",
        ttl: int = 5400,
        serializer: str = "json",
    ):
        """Initialize Redis cache."""
        self.client = redis.Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True if serializer == "json" else False,
        )
        self.prefix = prefix
        self.default_ttl = ttl
        self.serializer = serializer

    def _make_key(self, key: str) -> str:
        """Create a prefixed key to avoid collisions."""
        return f"{self.prefix}:{key}" if self.prefix else key

    def _serialize(self, value: T) -> Union[str, bytes]:
        """Serialize value based on chosen serializer."""
        if self.serializer == "json":
            return json.dumps(value)
        return pickle.dumps(value)

    def _deserialize(self, value: Union[str, bytes]) -> T:
        """Deserialize value based on chosen serializer."""
        if value is None:
            return None
        if self.serializer == "json":
            return json.loads(value)
        return pickle.loads(value)

    def get(self, key: str) -> Optional[T]:
        """Retrieve and deserialize a value from Redis."""
        try:
            value = self.client.get(self._make_key(key))
            return self._deserialize(value) if value is not None else None
        except Exception as e:
            logger.error(f"Cache error: {str(e)}")
            return None

    def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Store a serialized value in Redis with optional TTL."""
        try:
            key = self._make_key(key)
            serialized = self._serialize(value)
            if ttl is not None:
                return self.client.setex(key, ttl, serialized)
            return self.client.set(key, serialized)
        except Exception as e:
            logger.error(f"Cache error: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Remove a value from Redis."""
        try:
            return bool(self.client.delete(self._make_key(key)))
        except Exception as e:
            logger.error(f"Cache error: {str(e)}")
            return False

    async def start(self) -> None:
        """Initialize Redis connection"""
        try:
            self.client.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    async def stop(self) -> None:
        """Cleanup Redis connection"""
        try:
            self.client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")
