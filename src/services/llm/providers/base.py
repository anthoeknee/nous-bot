# src/services/llm/providers/base.py
from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from enum import Enum


class ModelCapabilities(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"
    FUNCTION_CALLING = "function_calling"


class LLMProvider(ABC):
    """Base interface for LLM providers"""

    @property
    @abstractmethod
    def capabilities(self) -> set[ModelCapabilities]:
        """Return set of supported capabilities"""
        pass

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    async def generate_with_images(
        self, prompt: str, images: list[bytes], **kwargs
    ) -> str:
        """Generate text from prompt and images"""
        pass

    @abstractmethod
    async def embed_text(self, text: str, **kwargs) -> list[float]:
        """Generate embeddings for text"""
        pass
