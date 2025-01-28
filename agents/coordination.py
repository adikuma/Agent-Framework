from typing import Any
class Blackboard:
    def __init__(self):
        self.data = {}
        
    def post(self, key: str, value: Any):
        pass
    
    def get(self, key: str) -> Any:
        pass

class Task:
    def __init__(self, description: str, priority: int = 1):
        self.description = description
        self.priority = priority
        self.dependencies = []