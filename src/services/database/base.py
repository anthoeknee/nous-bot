"""Base classes and utilities for database models."""

from typing import TypeVar, Type, Optional, Any
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime

T = TypeVar("T")
Base = declarative_base()


class BaseModel(Base):
    """Base model class with common fields and utilities."""

    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    @classmethod
    def create(cls: Type[T], session: Any, **kwargs) -> T:
        """Create a new instance and add it to the session."""
        instance = cls(**kwargs)
        session.add(instance)
        return instance

    @classmethod
    def get(cls: Type[T], session: Any, id: int) -> Optional[T]:
        """Get an instance by ID."""
        return session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_all(cls: Type[T], session: Any) -> list[T]:
        """Get all instances."""
        return session.query(cls).all()

    def update(self, session: Any, **kwargs) -> None:
        """Update instance attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

    def delete(self, session: Any) -> None:
        """Delete the instance."""
        session.delete(self)
