from typing import Dict, Type, Optional, Any
from sqlalchemy.orm import DeclarativeBase

from .main import DatabaseService


class DatabaseManager:
    """
    Manages database connections and provides a high-level interface for database operations.
    Implements the Unit of Work pattern and manages database sessions.
    """

    def __init__(self, base_class: Type[DeclarativeBase]):
        self._db_service = DatabaseService()
        self._base_class = base_class
        self._repositories: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize the database service and create repositories"""
        await self._db_service.initialize(base_class=self._base_class)
        await self._db_service.start()
        self._init_repositories()

    def _init_repositories(self) -> None:
        """Initialize repositories for each model"""
        for model in self._base_class.__subclasses__():
            repository_name = f"{model.__name__.lower()}_repository"
            self._repositories[repository_name] = Repository(self._db_service, model)

    def __getattr__(self, name: str) -> "Repository":
        """Allow accessing repositories as attributes"""
        if name in self._repositories:
            return self._repositories[name]
        raise AttributeError(f"Repository '{name}' not found")

    async def cleanup(self) -> None:
        """Cleanup database resources"""
        await self._db_service.cleanup()

    @property
    def service(self) -> DatabaseService:
        """Get the underlying database service"""
        return self._db_service

    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        return await self._db_service.health_check()

    async def create_all(self) -> None:
        """Create all database tables"""
        async with self._db_service.session() as session:
            async with session.begin():
                await session.run_sync(self._base_class.metadata.create_all)

    async def drop_all(self) -> None:
        """Drop all database tables"""
        async with self._db_service.session() as session:
            async with session.begin():
                await session.run_sync(self._base_class.metadata.drop_all)


class Repository:
    """
    Generic repository for database operations on a specific model.
    Provides a high-level interface for common database operations.
    """

    def __init__(self, db_service: DatabaseService, model_class: Type[DeclarativeBase]):
        self._db = db_service
        self._model = model_class

    async def get(self, id: Any) -> Optional[DeclarativeBase]:
        """Get entity by ID"""
        return await self._db.get_by_id(self._model, id)

    async def get_all(self, **filters) -> list[DeclarativeBase]:
        """Get all entities matching filters"""
        async with self._db.session() as session:
            query = session.query(self._model)
            for key, value in filters.items():
                query = query.filter(getattr(self._model, key) == value)
            result = await session.execute(query)
            return result.scalars().all()

    async def create(self, **kwargs) -> DeclarativeBase:
        """Create new entity"""
        instance = self._model(**kwargs)
        return await self._db.create(instance)

    async def update(self, id: Any, **kwargs) -> Optional[DeclarativeBase]:
        """Update entity by ID"""
        instance = await self.get(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            return await self._db.update(instance)
        return None

    async def delete(self, id: Any) -> bool:
        """Delete entity by ID"""
        instance = await self.get(id)
        if instance:
            return await self._db.delete(instance)
        return False

    async def count(self, **filters) -> int:
        """Count entities matching filters"""
        return await self._db.count(self._model, **filters)

    async def exists(self, **filters) -> bool:
        """Check if entity exists with given filters"""
        return await self._db.exists(self._model, **filters)

    async def bulk_create(self, items: list[Dict[str, Any]]) -> list[DeclarativeBase]:
        """Bulk create entities"""
        instances = [self._model(**item) for item in items]
        return await self._db.bulk_create(instances)

    async def bulk_update(self, filters: Dict[str, Any], values: Dict[str, Any]) -> int:
        """Bulk update entities matching filters"""
        return await self._db.bulk_update(self._model, values, **filters)

    async def bulk_delete(self, **filters) -> int:
        """Bulk delete entities matching filters"""
        return await self._db.bulk_delete(self._model, **filters)
