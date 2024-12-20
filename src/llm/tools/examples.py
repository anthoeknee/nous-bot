from .registry import ToolRegistry, ToolParameter, ParameterType

# Create registry instance
tools = ToolRegistry()


# Example 1: Register a tool using the decorator with automatic parameter inference
@tools.register_function(
    name="calculate", description="Evaluate a mathematical expression"
)
def calculate(expression: str) -> float:
    try:
        return float(eval(expression))
    except:
        raise ValueError("Invalid expression")


# Example 2: Register a weather tool with explicit parameters
@tools.register_function(
    name="get_weather",
    description="Get the current weather for a location",
    parameters=[
        ToolParameter(
            name="location",
            type=ParameterType.STRING,
            description="The city and state, e.g. San Francisco, CA",
        ),
        ToolParameter(
            name="unit",
            type=ParameterType.STRING,
            description="Temperature unit",
            required=False,
            enum=["celsius", "fahrenheit"],
        ),
    ],
)
def get_weather(location: str, unit: str = "fahrenheit") -> dict:
    # Mock implementation
    return {
        "temperature": 72 if unit == "fahrenheit" else 22,
        "condition": "sunny",
        "location": location,
    }
