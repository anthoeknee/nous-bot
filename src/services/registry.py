from typing import Dict, Type, Any
from .interface import ServiceInterface


class ServiceRegistry:
    """
    Service registry for dependency injection and service management.
    Implements the Service Locator pattern.
    """

    _instance = None
    _services: Dict[str, Any] = {}
    _implementations: Dict[str, Type[ServiceInterface]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register_implementation(
        cls, service_name: str, implementation: Type[ServiceInterface]
    ) -> None:
        """Register a service implementation"""
        cls._implementations[service_name] = implementation

    @classmethod
    def get_implementation(cls, service_name: str) -> Type[ServiceInterface]:
        """Get a service implementation"""
        if service_name not in cls._implementations:
            raise KeyError(f"No implementation registered for service: {service_name}")
        return cls._implementations[service_name]

    @classmethod
    def register_instance(cls, service_name: str, instance: Any) -> None:
        """Register a service instance"""
        cls._services[service_name] = instance

    @classmethod
    def get_instance(cls, service_name: str) -> Any:
        """Get a service instance"""
        if service_name not in cls._services:
            raise KeyError(f"No instance registered for service: {service_name}")
        return cls._services[service_name]

    @classmethod
    def has_instance(cls, service_name: str) -> bool:
        """Check if a service instance exists"""
        return service_name in cls._services

    @classmethod
    def clear(cls) -> None:
        """Clear all registered services"""
        cls._services.clear()
        cls._implementations.clear()
