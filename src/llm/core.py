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
from src.llm.routing.intent_router import route_request  # Example usage


class LLMCore:
    """
    LLMCore wraps all the major components needed to handle LLM interactions.
    """

    def __init__(self, session_id: str, redis_cache):
        self.session_id = session_id
        self.short_term_memory = ShortTermMemory(session_id, redis_cache)
        self.tool_registry = ToolRegistry()
        self.provider = GroqProvider(tool_registry=self.tool_registry)

    async def process_user_message(self, message: dict) -> str:
        """Process user message, handling both text and images."""

        # If message contains an image, process it first
        if message.get("type") == "image_url":
            # The image description will be automatically handled in the provider
            pass

        # Store user message (original message with image URL if present)
        await self.short_term_memory.add_message(
            "user", message.get("content", ""), extra=message
        )

        # Gather conversation history
        conversation_history = await self.short_term_memory.get_history()

        # Build any tool definitions
        tools_for_llm = self.tool_registry.build_tools_for_groq()

        # Route the request to correct model
        response_text = route_request(
            conversation_history, self.provider, tools=tools_for_llm
        )

        # Save the assistant response
        await self.short_term_memory.add_message("assistant", response_text)

        return response_text
