# src/services/llm/factory.py
from typing import Dict, Type
from .providers.base import LLMProvider
from .providers.google import GoogleProvider


class LLMFactory:
    """Factory for creating LLM provider instances"""

    _providers: Dict[str, Type[LLMProvider]] = {
        "google": GoogleProvider,
        # Add other providers here
    }

    @classmethod
    def create(cls, provider: str, **config) -> LLMProvider:
        """Create a new LLM provider instance"""
        if provider not in cls._providers:
            raise ValueError(f"Unknown provider: {provider}")

        provider_class = cls._providers[provider]
        return provider_class(**config)

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[LLMProvider]) -> None:
        """Register a new provider class"""
        cls._providers[name] = provider_class
