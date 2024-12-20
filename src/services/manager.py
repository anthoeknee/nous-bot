from typing import Dict, Type, Optional
import logging
from contextlib import asynccontextmanager

from .base import BaseService
from .cache.main import RedisCache
from .database.manager import DatabaseManager
from src.core.exceptions import ServiceError


class ServiceManager:
    """
    Manages all application services and their lifecycle.
    Provides a central point for service access and management.
    """

    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._initialized = False
        self._logger = logging.getLogger(__name__)

    async def initialize(self, database_base: Optional[Type] = None) -> None:
        """Initialize all services"""
        if self._initialized:
            return

        try:
            # Initialize cache service
            cache_service = RedisCache()
            await cache_service.initialize()
            self._services["cache"] = cache_service

            # Initialize database service if base class provided
            if database_base:
                db_manager = DatabaseManager(database_base)
                await db_manager.initialize()
                self._services["database"] = db_manager

            # Initialize other services as needed

            # Start all services
            for name, service in self._services.items():
                await service.start()
                self._logger.info(f"Service '{name}' started successfully")

            self._initialized = True
            self._logger.info("All services initialized successfully")

        except Exception as e:
            self._logger.error(f"Failed to initialize services: {e}")
            await self.cleanup()
            raise ServiceError(f"Service initialization failed: {str(e)}") from e

    async def cleanup(self) -> None:
        """Cleanup all services"""
        for name, service in reversed(list(self._services.items())):
            try:
                await service.cleanup()
                self._logger.info(f"Service '{name}' cleaned up successfully")
            except Exception as e:
                self._logger.error(f"Failed to cleanup service '{name}': {e}")

        self._services.clear()
        self._initialized = False

    async def health_check(self) -> Dict[str, Dict]:
        """Perform health check on all services"""
        results = {}
        for name, service in self._services.items():
            try:
                results[name] = await service.health_check()
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        return results

    def get_service(self, name: str) -> Optional[BaseService]:
        """Get service by name"""
        return self._services.get(name)

    @property
    def cache(self) -> RedisCache:
        """Get cache service"""
        return self._services["cache"]

    @property
    def database(self) -> DatabaseManager:
        """Get database manager"""
        return self._services["database"]

    @asynccontextmanager
    async def session(self):
        """Get database session"""
        if "database" not in self._services:
            raise ServiceError("Database service not initialized")
        async with self.database.service.session() as session:
            yield session

    @asynccontextmanager
    async def transaction(self):
        """Get database transaction"""
        if "database" not in self._services:
            raise ServiceError("Database service not initialized")
        async with self.database.service.transaction() as session:
            yield session
