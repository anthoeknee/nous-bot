from typing import List, Dict, Any, Optional
import json
from groq import Groq

from .base import BaseProvider  # Assuming you have a simple base class
from src.llm.tools.registry import ToolRegistry


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

    def _prepare_groq_messages(
        self, conversation_history: List[Dict[str, Any]]
    ) -> List[Dict]:
        """
        Convert the internal conversation structure into the format Groq expects.
        If a message is an image, we embed it with type="image_url".
        Otherwise we embed text with type="text".
        """
        groq_messages = []
        for entry in conversation_history:
            if entry.get("type") == "image_url":
                # Convert the user entry with an image field
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
                # Normal text message
                groq_messages.append(
                    {"role": entry["role"], "content": entry["content"]}
                )
        return groq_messages

    def generate_response(
        self,
        conversation_history: List[Dict[str, Any]],
        use_vision_model: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate a response from Groq. If use_vision_model is True, we call the vision model,
        otherwise we call the text/tool model. If tools are provided, they will be passed
        to the Groq API. This method automatically resolves any tool calls returned by the model.
        """
        model_to_use = self.vision_model if use_vision_model else self.text_model
        groq_messages = self._prepare_groq_messages(conversation_history)

        # If we have a tool registry, build full tool definitions
        tool_definitions = tools if tools else []
        if self.tool_registry:
            # Merge any externally passed-in tools with the registry
            # (the external ones might or might not be relevant - up to you).
            registry_tools = self.tool_registry.build_tools_for_groq()
            tool_definitions = (tool_definitions or []) + registry_tools

        response = self.client.chat.completions.create(
            model=model_to_use,
            messages=groq_messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False,
            tools=tool_definitions if len(tool_definitions) > 0 else None,
            tool_choice="auto" if len(tool_definitions) > 0 else None,
        )

        # If there's at least one choice, interpret the assistant message
        if not response.choices:
            return "<NO_RESPONSE>"

        main_msg = response.choices[0].message
        # Process potential tool calls
        if hasattr(main_msg, "tool_calls") and main_msg.tool_calls:
            # We'll add the LLM's message to conversation
            conversation_history.append(
                {"role": "assistant", "content": "Tool call triggered."}
            )
            # For each tool call, attempt to resolve and call the python function
            for call_item in main_msg.tool_calls:
                tool_name = call_item.function.name
                arguments_json = call_item.function.arguments
                function_output = self.tool_registry.resolve_and_invoke(
                    tool_name, arguments_json
                )

                # Insert the tool's result as a "tool" or "system" role message
                conversation_history.append(
                    {
                        "role": "tool",
                        "name": tool_name,
                        "content": function_output,
                    }
                )

            # After we've appended tool responses, we make a second request to finalize the outcome
            new_groq_messages = self._prepare_groq_messages(conversation_history)
            second_response = self.client.chat.completions.create(
                model=model_to_use,
                messages=new_groq_messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False,
            )
            if second_response.choices and second_response.choices[0].message:
                return second_response.choices[0].message.content or "<NO_RESPONSE>"

            return "<NO_RESPONSE>"

        # Otherwise, no tool calls. Return direct content.
        if isinstance(main_msg.content, list):
            # If Groq returns a structured list content, flatten it
            combined = " ".join(
                seg.get("text", "")
                for seg in main_msg.content
                if seg.get("type") == "text"
            )
            return combined.strip()

        return main_msg.content or "<NO_RESPONSE>"
