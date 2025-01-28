from typing import Dict
from typing import List
from tools.base import BaseTool

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        
    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool
        
    def get_tool(self, name: str) -> BaseTool:
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict]:
        return [{"name": t.name, "description": t.description} 
                for t in self.tools.values()]