# src/services/llm/providers/google.py
from typing import Optional, Any
from google import genai
from google.genai import types

from .base import LLMProvider, ModelCapabilities
from src.utils.logging import get_logger

logger = get_logger()


class GoogleProvider(LLMProvider):
    """Google GenAI provider implementation"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    @property
    def capabilities(self) -> set[ModelCapabilities]:
        return {
            ModelCapabilities.TEXT,
            ModelCapabilities.IMAGE,
            ModelCapabilities.CODE,
            ModelCapabilities.FUNCTION_CALLING,
        }

    async def generate_text(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(**kwargs),
            )
            return response.text
        except Exception as e:
            logger.error(f"Google text generation error: {str(e)}")
            raise

    async def generate_with_images(
        self, prompt: str, images: list[bytes], **kwargs
    ) -> str:
        try:
            contents = [
                types.Part.from_text(prompt),
                *[types.Part.from_bytes(img, mime_type="image/jpeg") for img in images],
            ]

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(**kwargs),
            )
            return response.text
        except Exception as e:
            logger.error(f"Google multimodal generation error: {str(e)}")
            raise

    async def embed_text(self, text: str, **kwargs) -> list[float]:
        try:
            response = self.client.models.embed_content(
                model="text-embedding-004",  # Using Google's embedding model
                contents=text,
                config=types.EmbedContentConfig(**kwargs),
            )
            return response.embeddings[0]
        except Exception as e:
            logger.error(f"Google embedding error: {str(e)}")
            raise
