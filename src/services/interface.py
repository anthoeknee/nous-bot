from abc import ABC, abstractmethod
from typing import Any, Dict
from enum import Enum


class ServiceStatus(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ServiceInterface(ABC):
    """Enhanced interface for all services"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Service name"""
        pass

    @property
    @abstractmethod
    def status(self) -> ServiceStatus:
        """Current service status"""
        pass

    @abstractmethod
    async def initialize(self, **kwargs) -> None:
        """Initialize the service"""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the service"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the service"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass
