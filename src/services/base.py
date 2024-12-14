# src/services/base.py
from abc import ABC, abstractmethod


class ServiceInterface(ABC):
    """Base interface for all services"""

    @abstractmethod
    async def start(self) -> None:
        """Initialize the service"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Cleanup and shutdown the service"""
        pass
