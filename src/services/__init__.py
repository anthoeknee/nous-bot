# src/services/__init__.py
from .manager import ServiceManager


def get_services() -> ServiceManager:
    """Get the global service manager instance"""
    return ServiceManager.get_instance()
