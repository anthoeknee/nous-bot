from typing import Optional, Union, TypeVar
import json
import pickle
import redis

from src.core.config import Config
from .interface import CacheInterface
from src.services.base import ServiceInterface

T = TypeVar("T")


class RedisCache(CacheInterface[T], ServiceInterface):
    """Redis-based cache implementation with flexible serialization."""

    def __init__(self, prefix: str = "", serializer: str = "json"):
        """
        Initialize Redis cache with configuration from Config singleton.

        Args:
            prefix: Prefix for all cache keys to avoid collisions
            serializer: Serialization method ('json' or 'pickle')
        """
        config = Config.get().redis
        self.client = redis.Redis(
            host=config.host,
            port=config.port,
            password=config.password,
            decode_responses=True if serializer == "json" else False,
        )
        self.prefix = prefix
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
        except (redis.RedisError, json.JSONDecodeError, pickle.PickleError) as e:
            # Log error here if needed
            return None

    def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Store a serialized value in Redis with optional TTL."""
        try:
            key = self._make_key(key)
            serialized = self._serialize(value)
            if ttl is not None:
                return self.client.setex(key, ttl, serialized)
            return self.client.set(key, serialized)
        except (redis.RedisError, json.JSONDecodeError, pickle.PickleError):
            return False

    def delete(self, key: str) -> bool:
        """Remove a value from Redis."""
        try:
            return bool(self.client.delete(self._make_key(key)))
        except redis.RedisError:
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            return bool(self.client.exists(self._make_key(key)))
        except redis.RedisError:
            return False

    def set_many(self, mapping: dict[str, T], ttl: Optional[int] = None) -> bool:
        """Store multiple key-value pairs in Redis."""
        try:
            pipeline = self.client.pipeline()
            for key, value in mapping.items():
                key = self._make_key(key)
                serialized = self._serialize(value)
                if ttl is not None:
                    pipeline.setex(key, ttl, serialized)
                else:
                    pipeline.set(key, serialized)
            pipeline.execute()
            return True
        except redis.RedisError:
            return False

    def get_many(self, keys: list[str]) -> dict[str, Optional[T]]:
        """Retrieve multiple values from Redis."""
        try:
            pipeline = self.client.pipeline()
            prefixed_keys = [self._make_key(key) for key in keys]
            for key in prefixed_keys:
                pipeline.get(key)
            values = pipeline.execute()
            return {
                key: self._deserialize(value) if value is not None else None
                for key, value in zip(keys, values)
            }
        except redis.RedisError:
            return {key: None for key in keys}

    async def start(self) -> None:
        # Initialize Redis connection
        await self.client.ping()

    async def stop(self) -> None:
        # Close Redis connection
        await self.client.close()
