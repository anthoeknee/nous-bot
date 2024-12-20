from typing import List, Dict, Any
from src.llm.providers.groq import GroqProvider


def decide_model(conversation_history: List[Dict[str, Any]]) -> bool:
    """
    Determines if the request should go to the vision model (True) or text model (False).
    Checks if the last user message is referencing an image.
    """
    if not conversation_history:
        return False

    last_message = conversation_history[-1]
    # If the last user message is an image request, route to the vision model
    if last_message.get("role") == "user" and last_message.get("type") == "image_url":
        return True

    return False


def route_request(
    conversation_history: List[Dict[str, Any]],
    groq_provider: GroqProvider,
    tools: List[Dict[str, Any]] = None,
) -> str:
    """
    Routes the request to the appropriate Groq model based on decide_model's output
    and returns the text response from the LLM.
    """
    use_vision = decide_model(conversation_history)
    return groq_provider.generate_response(
        conversation_history,
        use_vision_model=use_vision,
        tools=tools,
    )
