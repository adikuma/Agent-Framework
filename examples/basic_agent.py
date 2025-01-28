import os 
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base import Agent
from tools.tool_registry import ToolRegistry
from memory.short_term import ShortTermMemory
from typing import Dict 
from providers.openai_provider import OpenAIProvider

class BasicAgent(Agent):
    def run(self, task: str) -> Dict:
        plan = self.plan(task)
        results = []
        for step in plan:
            result = self.execute_step(step)
            results.append(result)
        return self.format_output(results)
    
if __name__ == "__main__":
    llm = OpenAIProvider(model="gpt-3.5-turbo", api_key="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")
    tools = ToolRegistry()
    memory = ShortTermMemory()
    
    agent = BasicAgent(llm, tools, memory)
    response = agent.run("What's the weather in Tokyo?")
    print(response)