# src/services/manager.py
from typing import Optional, Dict, Type, Any
import importlib
from src.core.config import config
from src.utils.logging import get_logger

logger = get_logger()


class ServiceManager:
    """Manages all application services with dependency handling."""

    _instance: Optional["ServiceManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._services: Dict[str, Any] = {}
        self._initialized = True
        self._started = False

    @classmethod
    def get_instance(cls) -> "ServiceManager":
        return cls()

    async def initialize_services(self) -> None:
        """Initialize core services first, then others"""
        if self._started:
            return

        # Initialize core services first
        core_services = ["database", "cache"]

        for service_name in core_services:
            if service_name in config.SERVICES_CONFIG:
                await self._init_service(
                    service_name, config.SERVICES_CONFIG[service_name]
                )

        # Initialize remaining services
        for service_name, settings in config.SERVICES_CONFIG.items():
            if service_name not in core_services:
                await self._init_service(service_name, settings)

        self._started = True
        logger.info("All services initialized successfully")

    async def _init_service(self, service_name: str, settings: dict) -> None:
        """Initialize a single service"""
        if not settings.get("enabled", True):
            logger.info(f"Service {service_name} is disabled, skipping initialization")
            return

        try:
            # Import and instantiate the service
            module_path, class_name = settings["class"].rsplit(".", 1)
            module = importlib.import_module(module_path)
            service_class = getattr(module, class_name)

            service_instance = service_class(**settings.get("config", {}))

            # Start the service if it has a start method
            if hasattr(service_instance, "start"):
                await service_instance.start()

            self._services[service_name] = service_instance
            logger.info(f"Service {service_name} initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize service {service_name}: {str(e)}")
            raise

    def get_service(self, name: str) -> Any:
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
