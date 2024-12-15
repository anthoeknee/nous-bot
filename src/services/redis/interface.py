from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Callable, Any

T = TypeVar("T")


class RedisInterface(ABC):
    """Interface for Redis-based caching and events"""

    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """Retrieve a value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Store a value in cache with optional TTL in seconds."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove a value from cache."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Initialize the Redis connection."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Cleanup the Redis connection."""
        pass
