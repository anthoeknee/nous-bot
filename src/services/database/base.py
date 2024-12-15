"""Base classes and utilities for database models."""

from typing import TypeVar, Type, Optional, Any
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

T = TypeVar("T")
Base = declarative_base()


class BaseModel(Base):
    """Base model class with common fields and utilities."""

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    async def create(cls: Type[T], session: AsyncSession, **kwargs) -> T:
        """Create a new instance and add it to the session."""
        instance = cls(**kwargs)
        session.add(instance)
        await session.flush()
        return instance

    @classmethod
    async def get(cls: Type[T], session: AsyncSession, id: int) -> Optional[T]:
        """Get an instance by ID."""
        return await session.get(cls, id)

    @classmethod
    async def get_all(cls: Type[T], session: AsyncSession) -> list[T]:
        """Get all instances."""
        result = await session.execute(select(cls))
        return result.scalars().all()

    async def update(self, session: AsyncSession, **kwargs) -> None:
        """Update instance attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        await session.flush()

    async def delete(self, session: AsyncSession) -> None:
        """Delete the instance."""
        await session.delete(self)
        await session.flush()
