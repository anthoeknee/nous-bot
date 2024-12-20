from typing import List, Dict, Any, Optional
from groq import Groq
import json

from .base import BaseProvider  # Assuming you have a simple base class
from src.llm.tools.registry import ToolRegistry
from src.utils.logging import ColorLogger
from src.llm.personality import PersonalityEngine


class GroqProvider(BaseProvider):
    """
    GroqProvider handles LLM calls for both text-based and vision-based prompts
    using two different Groq models (one for text + tools and one for vision).
    It can maintain conversational context across calls, including images.

    • vision_model: llama-3.2-90b-vision-preview
    • text_model (also used for tool usage): llama-3.3-70b-versatile
    """

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        super().__init__()
        self.client = Groq()
        self.vision_model = "llama-3.2-90b-vision-preview"
        self.text_model = "llama-3.3-70b-versatile"
        self.tool_registry = tool_registry or ToolRegistry()
        self.logger = ColorLogger(__name__).getChild("groq")
        self.personality_engine = PersonalityEngine()

    def process_image(self, image_url: str) -> str:
        """Process an image URL and return a description."""
        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe what you see in this image, focusing on key elements, context, and any visible text.",
                            },
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
                temperature=0.7,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Image processing error: {str(e)}")
            return f"Error processing image: {str(e)}"

    def _prepare_groq_messages(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Prepare messages for Groq API format"""
        groq_messages = []

        # Generate dynamic system prompt based on current context
        session_data = {
            "message_count": len(messages),
            "tools_available": bool(self.tool_registry._tools),
        }
        system_prompt = self.personality_engine.render_system_prompt(session_data)
        groq_messages.append({"role": "system", "content": system_prompt})

        for message in messages:
            content = message.get("content", "")
            # Handle image messages by replacing with their description
            if message.get("type") == "image_url":
                image_description = self.process_image(message["url"])
                content = image_description

            prepared_message = {"role": message["role"], "content": content}
            groq_messages.append(prepared_message)

        return groq_messages

    def generate_response(
        self,
        messages: List[Dict[str, Any]],
        use_vision_model: bool = False,  # This parameter is now ignored
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> str:
        """Generate a response using the text model only."""
        try:
            groq_messages = self._prepare_groq_messages(messages)

            # Always use text model for final responses
            params = {
                "model": self.text_model,
                "messages": groq_messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096),
                "stream": False,
            }

            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            # Make initial API call
            response = self.client.chat.completions.create(**params)

            # Check for tool calls
            if hasattr(response.choices[0].message, "tool_calls"):
                tool_calls = response.choices[0].message.tool_calls
                if tool_calls:
                    # Add assistant's response with tool calls
                    groq_messages.append(response.choices[0].message)

                    # Process each tool call
                    for tool_call in tool_calls:
                        tool_result = self.tool_registry.resolve_and_invoke(
                            tool_call.function.name, tool_call.function.arguments
                        )

                        # Add tool result to messages
                        groq_messages.append(
                            {
                                "role": "tool",
                                "content": tool_result,
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                            }
                        )

                    # Make second API call with tool results
                    final_response = self.client.chat.completions.create(
                        model=self.text_model,
                        messages=groq_messages,
                        temperature=kwargs.get("temperature", 0.7),
                        max_tokens=kwargs.get("max_tokens", 4096),
                        stream=False,
                    )
                    return final_response.choices[0].message.content

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"Groq API error: {str(e)}")
            raise
