from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Generic

T = TypeVar("T")


class CacheInterface(ABC, Generic[T]):
    """Abstract base class for caching implementations."""

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
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        pass
