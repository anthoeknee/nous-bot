from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common database operations"""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: Any) -> Optional[ModelType]:
        """Get entity by ID"""
        return await self.session.get(self.model, id)

    async def get_all(self, **filters) -> List[ModelType]:
        """Get all entities matching filters"""
        query = select(self.model)
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        """Create new entity"""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        """Update entity by ID"""
        instance = await self.get(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
        return None

    async def delete(self, id: Any) -> bool:
        """Delete entity by ID"""
        instance = await self.get(id)
        if instance:
            await self.session.delete(instance)
            return True
        return False
