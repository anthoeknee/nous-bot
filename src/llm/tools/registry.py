import json
from typing import Callable, Dict, Any, List, Optional

"""
Tool Registry for automatically invoking python functions
from model-generated tool calls.

This registry will store references to python functions along with
the schema needed for Groq's tool call format. We'll feed these
tools into the LLM request. If the LLM calls a tool, we'll parse
the arguments and invoke the correct python function.
"""


class ToolRegistry:
    def __init__(self):
        # internal map from tool name to: { "function": fn, "description": ..., "schema": {...} }
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        function: Callable[..., Any],
        description: str,
        parameters_schema: Dict[str, Any],
    ) -> None:
        """
        Register a python function as a tool, with a name, description, and JSON schema.
        parameters_schema should follow:
            {
                "type": "object",
                "properties": {
                    "param": { "type": "string", "description": ... },
                    ...
                },
                "required": [...]
            }
        """
        self._tools[name] = {
            "function": function,
            "description": description,
            "schema": parameters_schema,
        }

    def build_tools_for_groq(self) -> List[Dict[str, Any]]:
        """
        Returns a groq-compatible list of tool definitions:
          [
            {
              "type": "function",
              "function": {
                "name": <tool_name>,
                "description": <description>,
                "parameters": <parameters_schema>
              }
            }, ...
          ]
        """
        results = []
        for name, info in self._tools.items():
            results.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": info["description"],
                        "parameters": info["schema"],
                    },
                }
            )
        return results

    def resolve_and_invoke(self, tool_name: str, arguments_json: str) -> str:
        """
        Parse the JSON arguments and call the underlying python function.
        Return the function's stringified result for the LLM conversation.
        """
        if tool_name not in self._tools:
            return json.dumps({"error": f"No tool named '{tool_name}' is registered."})

        fn = self._tools[tool_name]["function"]
        try:
            parsed_args = json.loads(arguments_json)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Failed to parse JSON arguments: {str(e)}"})

        try:
            result = fn(**parsed_args)
            # Encourage returning JSON for clarity
            return json.dumps({"result": result})
        except Exception as e:
            return json.dumps(
                {"error": f"Exception running tool '{tool_name}': {str(e)}"}
            )
