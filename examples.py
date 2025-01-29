from tool import Tool
from core import Agent
from openai_provider import OpenAIProvider

def get_current_weather(location: str) -> str:
    return f"Weather in {location}: 72°F, sunny"

tools = [
    Tool(
        name="get_current_weather",
        description="Get the current weather in a given location",
        func=get_current_weather
    )
]

# example output schema
output_schema = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number"}
    },
    "required": ["answer"]
}

agent = Agent(
    llm_provider=OpenAIProvider(model = "gpt-3.5-turbo", api_key = "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"),
    tools=tools,
    output_schema=output_schema
)

# simple query without tool usage
print(agent.run("What is the capital of France?"))
