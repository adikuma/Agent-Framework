from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any

class ToolInput(BaseModel):
    parameters: dict
    user_id: str = None

class BaseTool(ABC):
    name: str
    description: str
    
    @abstractmethod
    def execute(self, input: ToolInput) -> Any:
        pass