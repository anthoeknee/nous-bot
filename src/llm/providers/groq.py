from typing import List, Dict, Any, Optional
from groq import Groq

from .base import BaseProvider  # Assuming you have a simple base class
from src.llm.tools.registry import ToolRegistry
from src.utils.logging import ColorLogger


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

    def _prepare_groq_messages(
        self, conversation_history: List[Dict[str, Any]]
    ) -> List[Dict]:
        """
        Convert the internal conversation structure into the format Groq expects.
        Handles both text and image messages.
        """
        groq_messages = []
        for entry in conversation_history:
            # Create a clean message with only the required fields
            if entry.get("type") == "image_url":
                groq_messages.append(
                    {
                        "role": entry["role"],
                        "content": [
                            {
                                "type": "text",
                                "text": entry.get("content", "Analyze this image:"),
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": entry["url"]},
                            },
                        ],
                    }
                )
            else:
                # For text messages, only include role and content
                groq_messages.append(
                    {"role": entry["role"], "content": entry["content"]}
                )

        return groq_messages

    def generate_response(
        self,
        messages: List[Dict[str, Any]],
        use_vision_model: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> str:
        """Generate a response using the appropriate Groq model."""
        try:
            groq_messages = self._prepare_groq_messages(messages)

            # Set up base parameters
            params = {
                "model": self.vision_model if use_vision_model else self.text_model,
                "messages": groq_messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096),
                "stream": False,
            }

            # Only add tools if using text model (vision model doesn't support tools)
            if tools and not use_vision_model:
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
