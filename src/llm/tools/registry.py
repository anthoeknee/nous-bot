from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass
import json
import inspect
from enum import Enum


class ParameterType(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    name: str
    type: ParameterType
    description: str
    required: bool = True
    enum: List[str] = None


class Tool:
    def __init__(
        self,
        name: str,
        function: Callable,
        description: str,
        parameters: List[ToolParameter],
    ):
        self.name = name
        self.function = function
        self.description = description
        self.parameters = parameters

    def to_groq_schema(self) -> Dict[str, Any]:
        """Convert tool definition to Groq-compatible schema"""
        properties = {}
        required = []

        for param in self.parameters:
            param_schema = {"type": param.type.value, "description": param.description}
            if param.enum:
                param_schema["enum"] = param.enum

            properties[param.name] = param_schema

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a new tool"""
        self._tools[tool.name] = tool

    def register_function(
        self, name: str, description: str, parameters: List[ToolParameter] = None
    ) -> Callable:
        """Decorator to register a function as a tool"""

        def decorator(func: Callable) -> Callable:
            # If no parameters provided, attempt to infer from function signature
            if parameters is None:
                sig = inspect.signature(func)
                inferred_params = []
                for param_name, param in sig.parameters.items():
                    # Basic type inference - could be expanded
                    param_type = ParameterType.STRING  # default
                    if param.annotation in (int, float):
                        param_type = ParameterType.NUMBER
                    elif param.annotation == bool:
                        param_type = ParameterType.BOOLEAN

                    inferred_params.append(
                        ToolParameter(
                            name=param_name,
                            type=param_type,
                            description=f"Parameter {param_name}",
                            required=param.default == inspect.Parameter.empty,
                        )
                    )
                tool_params = inferred_params
            else:
                tool_params = parameters

            tool = Tool(name, func, description, tool_params)
            self.register(tool)
            return func

        return decorator

    def build_tools_for_groq(self) -> List[Dict[str, Any]]:
        """Returns list of tool definitions in Groq-compatible format"""
        return [tool.to_groq_schema() for tool in self._tools.values()]

    def resolve_and_invoke(self, tool_name: str, arguments_json: str) -> str:
        """Invoke a tool with the provided arguments"""
        if tool_name not in self._tools:
            return json.dumps({"error": f"No tool named '{tool_name}' is registered"})

        tool = self._tools[tool_name]
        try:
            args = json.loads(arguments_json)
            result = tool.function(**args)
            return json.dumps({"result": result})
        except Exception as e:
            return json.dumps({"error": f"Error invoking {tool_name}: {str(e)}"})
