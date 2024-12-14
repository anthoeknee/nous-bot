from typing import Optional, Union, TypeVar, Callable, Any
import json
import pickle
import redis
import asyncio

from src.core.config import Config
from .interface import RedisInterface
from src.services.base import ServiceInterface
from src.utils.logging import get_logger

T = TypeVar("T")
logger = get_logger()


class RedisService(RedisInterface[T], ServiceInterface):
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
        self.pubsub = self.client.pubsub()
        self.prefix = prefix
        self.serializer = serializer
        self._subscriber_tasks = {}

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

    async def publish(self, channel: str, message: Any) -> None:
        """Publish message to a channel"""
        try:
            serialized = self._serialize(message)
            await self.client.publish(channel, serialized)
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")

    async def subscribe(
        self, channel: str, handler: Callable[[str, Any], None]
    ) -> None:
        """Subscribe to a channel with a handler"""
        try:
            await self.pubsub.subscribe(channel)

            async def message_handler():
                while True:
                    message = await self.pubsub.get_message()
                    if message and message["type"] == "message":
                        data = self._deserialize(message["data"])
                        await handler(channel, data)

            # Store task reference for cleanup
            self._subscriber_tasks[channel] = asyncio.create_task(message_handler())

        except Exception as e:
            logger.error(f"Failed to subscribe to channel: {e}")

    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel"""
        try:
            await self.pubsub.unsubscribe(channel)
            if channel in self._subscriber_tasks:
                self._subscriber_tasks[channel].cancel()
                del self._subscriber_tasks[channel]
        except Exception as e:
            logger.error(f"Failed to unsubscribe from channel: {e}")

    async def start(self) -> None:
        """Initialize Redis connection"""
        await self.client.ping()

    async def stop(self) -> None:
        """Cleanup Redis connection"""
        # Cancel all subscriber tasks
        for task in self._subscriber_tasks.values():
            task.cancel()
        self._subscriber_tasks.clear()

        # Close connections
        await self.pubsub.close()
        await self.client.close()
