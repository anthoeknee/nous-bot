from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Callable, Any

T = TypeVar("T")


class RedisInterface(ABC):
    """Combined interface for Redis-based caching and events"""

    # Cache methods
    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """Retrieve a value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Store a value in cache with optional TTL in seconds."""
        pass

    # Event methods
    @abstractmethod
    async def publish(self, channel: str, message: Any) -> None:
        """Publish message to a channel"""
        pass

    @abstractmethod
    async def subscribe(
        self, channel: str, handler: Callable[[str, Any], None]
    ) -> None:
        """Subscribe to a channel with a handler"""
        pass

    @abstractmethod
    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel"""
        pass
