import datetime
from typing import Any, Optional, Dict
import json
import pickle
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

from src.core import settings
from src.core.exceptions import CacheError
from ..base import BaseService
from .interface import CacheInterface


class RedisCache(BaseService, CacheInterface):
    """Enhanced Redis cache implementation with advanced features"""

    def __init__(self):
        super().__init__(name="redis_cache")
        self._pool: Optional[ConnectionPool] = None
        self._redis: Optional[redis.Redis] = None
        self._default_ttl = settings.redis_conversation_ttl
        self._namespace = "nexus:"  # Namespace to prevent key collisions

    async def _initialize(self, **kwargs) -> None:
        """Initialize Redis connection pool"""
        try:
            self._pool = redis.ConnectionPool(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                decode_responses=True,
                max_connections=50,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True,
                encoding="utf-8",
            )
        except Exception as e:
            raise CacheError(f"Failed to initialize Redis pool: {str(e)}") from e

    async def _start(self) -> None:
        """Create Redis client and verify connection"""
        try:
            self._redis = redis.Redis(connection_pool=self._pool)
            await self._redis.ping()
        except Exception as e:
            raise CacheError(f"Failed to start Redis client: {str(e)}") from e

    async def _stop(self) -> None:
        """Close Redis connections"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def _cleanup(self) -> None:
        """Cleanup Redis resources"""
        if self._pool:
            await self._pool.disconnect()
            self._pool = None

    def _build_key(self, key: str) -> str:
        """Build namespaced key"""
        return f"{self._namespace}{key}"

    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            value = await self._redis.get(self._build_key(key))
            return value
        except RedisError as e:
            self._logger.error(f"Redis GET error: {e}")
            raise CacheError(f"Failed to get key {key}: {str(e)}") from e

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set key-value pair with optional TTL"""
        try:
            return await self._redis.set(
                self._build_key(key), value, ex=ttl or self._default_ttl
            )
        except RedisError as e:
            self._logger.error(f"Redis SET error: {e}")
            raise CacheError(f"Failed to set key {key}: {str(e)}") from e

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(await self._redis.delete(self._build_key(key)))
        except RedisError as e:
            self._logger.error(f"Redis DELETE error: {e}")
            raise CacheError(f"Failed to delete key {key}: {str(e)}") from e

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(await self._redis.exists(self._build_key(key)))
        except RedisError as e:
            self._logger.error(f"Redis EXISTS error: {e}")
            raise CacheError(f"Failed to check existence of key {key}: {str(e)}") from e

    async def ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key"""
        try:
            ttl = await self._redis.ttl(self._build_key(key))
            return ttl if ttl > 0 else None
        except RedisError as e:
            self._logger.error(f"Redis TTL error: {e}")
            raise CacheError(f"Failed to get TTL for key {key}: {str(e)}") from e

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        try:
            return await self._redis.expire(self._build_key(key), ttl)
        except RedisError as e:
            self._logger.error(f"Redis EXPIRE error: {e}")
            raise CacheError(f"Failed to set expiry for key {key}: {str(e)}") from e

    async def clear(self) -> bool:
        """Clear all cache entries in the namespace"""
        try:
            keys = await self._redis.keys(f"{self._namespace}*")
            if keys:
                await self._redis.delete(*keys)
            return True
        except RedisError as e:
            self._logger.error(f"Redis CLEAR error: {e}")
            raise CacheError(f"Failed to clear cache: {str(e)}") from e

    # Advanced features

    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store JSON-serializable object"""
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, ttl)
        except (TypeError, json.JSONDecodeError) as e:
            raise CacheError(f"Failed to serialize JSON for key {key}: {str(e)}") from e

    async def get_json(self, key: str) -> Optional[Any]:
        """Retrieve and deserialize JSON object"""
        try:
            value = await self.get(key)
            return json.loads(value) if value else None
        except json.JSONDecodeError as e:
            raise CacheError(
                f"Failed to deserialize JSON for key {key}: {str(e)}"
            ) from e

    async def set_pickle(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store pickle-serialized object"""
        try:
            pickle_value = pickle.dumps(value)
            return await self._redis.set(
                self._build_key(key), pickle_value, ex=ttl or self._default_ttl
            )
        except pickle.PickleError as e:
            raise CacheError(f"Failed to pickle object for key {key}: {str(e)}") from e

    async def get_pickle(self, key: str) -> Optional[Any]:
        """Retrieve and unpickle object"""
        try:
            value = await self._redis.get(self._build_key(key))
            return pickle.loads(value) if value else None
        except pickle.PickleError as e:
            raise CacheError(
                f"Failed to unpickle object for key {key}: {str(e)}"
            ) from e

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return await self._redis.incrby(self._build_key(key), amount)
        except RedisError as e:
            raise CacheError(f"Failed to increment key {key}: {str(e)}") from e

    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement counter"""
        try:
            return await self._redis.decrby(self._build_key(key), amount)
        except RedisError as e:
            raise CacheError(f"Failed to decrement key {key}: {str(e)}") from e

    async def _health_check(self) -> Dict[str, Any]:
        """Perform Redis health check"""
        try:
            if not self._redis:
                return {"status": "error", "message": "Redis client not initialized"}

            # Check connection
            await self._redis.ping()

            # Get Redis info
            info = await self._redis.info()

            # Get namespace statistics
            namespace_keys = len(await self._redis.keys(f"{self._namespace}*"))

            return {
                "status": "healthy",
                "version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_connections_received": info.get("total_connections_received"),
                "total_commands_processed": info.get("total_commands_processed"),
                "namespace_keys": namespace_keys,
                "uptime_seconds": info.get("uptime_in_seconds"),
            }
        except RedisError as e:
            return {
                "status": "error",
                "message": str(e),
                "last_error_timestamp": datetime.now().isoformat(),
            }
