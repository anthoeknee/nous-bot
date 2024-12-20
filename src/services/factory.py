from typing import Type, TypeVar, Dict, Any
from src.utils.factory import Factory
from .interface import ServiceInterface
from .registry import ServiceRegistry
from src.core.exceptions import ServiceError

T = TypeVar("T", bound=ServiceInterface)


class ServiceFactory:
    """
    Factory for creating service instances.
    Uses the base Factory class for service creation.
    """

    _factory = Factory()

    @classmethod
    def register_service(cls, name: str, service_class: Type[T]) -> None:
        """Register a service creator function"""

        async def creator(**kwargs) -> T:
            try:
                service = service_class()
                await service.initialize(**kwargs)
                ServiceRegistry.register_instance(name, service)
                return service
            except Exception as e:
                raise ServiceError(f"Failed to create service {name}: {str(e)}") from e

        cls._factory.register(name, creator)

    @classmethod
    async def create_service(cls, name: str, **kwargs) -> T:
        """Create a service instance using the registered creator"""
        try:
            creator = cls._factory.create(name, **kwargs)
            return await creator
        except ValueError as e:
            raise ServiceError(f"No service registered with name: {name}") from e

    @classmethod
    async def create_services(
        cls, services: Dict[str, Dict[str, Any]]
    ) -> Dict[str, ServiceInterface]:
        """Create multiple services from configuration"""
        created_services = {}

        for service_name, config in services.items():
            try:
                service = await cls.create_service(
                    service_name, **config.get("options", {})
                )
                created_services[service_name] = service

            except Exception as e:
                # Cleanup created services on failure
                for created_service in created_services.values():
                    await created_service.cleanup()
                raise ServiceError(
                    f"Failed to create service {service_name}: {str(e)}"
                ) from e

        return created_services
