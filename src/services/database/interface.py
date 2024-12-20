from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class DatabaseInterface(ABC, Generic[T]):
    """Interface for database operations"""

    @abstractmethod
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        pass

    @abstractmethod
    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute raw SQL query"""
        pass

    @abstractmethod
    async def get_by_id(self, model: T, id: Any) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def create(self, model: T) -> T:
        """Create new entity"""
        pass

    @abstractmethod
    async def update(self, model: T) -> T:
        """Update existing entity"""
        pass

    @abstractmethod
    async def delete(self, model: T) -> bool:
        """Delete entity"""
        pass
