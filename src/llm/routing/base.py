class BaseRouter:
    """
    BaseRouter provides a common structure for routing requests between
    multiple LLM providers or models. It should define a route_request()
    method that decides which model or flow to invoke and returns the result.
    """

    def route_request(self, conversation_history, llm_provider, tools=None):
        """
        Perform the routing logic and return the text response from the chosen LLM.
        Base implementation is abstract—must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement 'route_request' method")
