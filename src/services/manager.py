# src/services/manager.py
from typing import Dict, Any
import asyncio
from src.utils.logging import get_logger
from src.core.config import config
from .base import ServiceInterface

logger = get_logger()


class ServiceManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._services = {}
            cls._instance._initialized = False
        return cls._instance

    _services: Dict[str, ServiceInterface]

    @classmethod
    def get_instance(cls):
        return cls() if cls._instance is None else cls._instance

    async def initialize_services(self) -> None:
        """Initialize all enabled services in parallel."""
        if self._initialized:
            return

        service_configs = config.SERVICES_CONFIG
        init_tasks = []

        for service_name, service_config in service_configs.items():
            if not service_config.get("enabled", True):
                continue

            try:
                # Dynamically import and instantiate service
                module_path, class_name = service_config["class"].rsplit(".", 1)
                module = __import__(module_path, fromlist=[class_name])
                service_class = getattr(module, class_name)

                # Create service instance
                service = service_class(**service_config.get("config", {}))
                self._services[service_name] = service

                # Add initialization task
                init_tasks.append(service.start())

            except Exception as e:
                logger.error(f"Failed to create service {service_name}: {e}")
                raise

        # Initialize all services in parallel
        if init_tasks:
            await asyncio.gather(*init_tasks)

        self._initialized = True
        logger.info("All services initialized")

    def get_service(self, name: str) -> ServiceInterface:
        """Get a service by name"""
        if name not in self._services:
            raise KeyError(f"Service {name} not found")
        return self._services[name]

    @property
    def cache(self):
        """Quick access to cache service"""
        return self.get_service("cache")

    @property
    def db(self):
        """Quick access to database service"""
        return self.get_service("database")

    async def stop_all(self) -> None:
        """Stop all services in reverse initialization order"""
        for name, service in reversed(list(self._services.items())):
            try:
                if hasattr(service, "stop"):
                    await service.stop()
                logger.info(f"Service {name} stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping service {name}: {str(e)}")
