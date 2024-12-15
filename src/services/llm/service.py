# src/services/llm/service.py
from typing import Optional
from src.services.base import ServiceInterface
from src.utils.logging import get_logger
from .factory import LLMFactory
from .providers.base import LLMProvider

logger = get_logger()


class LLMService(ServiceInterface):
    """Service for managing LLM providers"""

    def __init__(self, default_provider: str, provider_configs: dict):
        """Initialize LLM service with configuration."""
        self.provider_configs = provider_configs
        self.default_provider = default_provider
        self._providers: dict[str, LLMProvider] = {}

    async def start(self) -> None:
        """Initialize default provider"""
        try:
            self.get_provider(self.default_provider)
            logger.info(
                f"LLM service started with default provider: {self.default_provider}"
            )
        except Exception as e:
            logger.error(f"Failed to start LLM service: {str(e)}")
            raise

    async def stop(self) -> None:
        """Cleanup providers"""
        self._providers.clear()
        logger.info("LLM service stopped")

    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        """Get or create a provider instance"""
        provider_name = name or self.default_provider

        if provider_name not in self._providers:
            if provider_name not in self.provider_configs:
                raise ValueError(
                    f"No configuration found for provider: {provider_name}"
                )

            config = self.provider_configs[provider_name]
            self._providers[provider_name] = LLMFactory.create(provider_name, **config)

        return self._providers[provider_name]
