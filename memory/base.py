from abc import ABC, abstractmethod
from typing import Any, List

# base memory
# handles the storage and retrieval of data
# like a chat history
class BaseMemory(ABC):
    @abstractmethod
    def add(self, item: Any):
        pass
    
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[Any]:
        pass
    
    @abstractmethod
    def clear(self):
        pass
