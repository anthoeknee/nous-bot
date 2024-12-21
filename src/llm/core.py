"""
core.py consolidates the logic of setting up and using the LLM modules:
  - short_term memory
  - tool registry
  - providers for vision and text
  - routing
  - etc.
"""

from src.llm.memory.short_term import ShortTermMemory
from src.llm.tools.registry import ToolRegistry
from src.llm.providers.groq import GroqProvider
from typing import Optional, Dict, Any

from src.services.cache.main import RedisCache


class LLMCore:
    """
    LLMCore wraps all the major components needed to handle LLM interactions.
    """

    def __init__(
        self,
        session_id: str,
        cache: RedisCache,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        self.session_id = session_id
        self.cache = cache
        self.memory = ShortTermMemory(session_id, cache)
        # Initialize provider with tools
        self.provider = GroqProvider(tool_registry=tool_registry)

    async def process_user_message(self, message: Dict[str, Any]) -> str:
        """Process user message, handling both text and images."""

        # If message contains an image, process it first
        if message.get("type") == "image_url":
            # The image description will be automatically handled in the provider
            pass

        # Store user message
        await self.memory.add_message("user", message.get("content", ""), extra=message)

        # Gather conversation history
        conversation_history = await self.memory.get_history()

        # Build any tool definitions
        tools = None
        if hasattr(self.provider, "tool_registry") and self.provider.tool_registry:
            tools = self.provider.tool_registry.build_tools_for_groq()

        # Generate response directly (no routing needed)
        response = await self.provider.generate_response(
            messages=conversation_history, tools=tools
        )

        # Save the assistant response
        await self.memory.add_message("assistant", response)

        return response
