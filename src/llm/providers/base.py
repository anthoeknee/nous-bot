class BaseProvider:
    """
    BaseProvider gives a standard interface for any LLM provider integration.

    Subclasses should override generate_response() to handle actual LLM calls.
    """

    def __init__(self):
        pass

    def generate_response(
        self, conversation_history, use_vision_model=False, tools=None
    ):
        """
        Generate a text response from the conversation_history and optional tools.
        This base method is abstract—must be overridden by subclasses.
        """
        raise NotImplementedError(
            "Subclasses must implement 'generate_response' method"
        )
