from typing import Any, List
from .base import BaseMemory


# short-term memory implementation using a rolling buffer
class ShortTermMemory(BaseMemory):
    def __init__(self, max_size: int = 10):
        self.buffer: List[Any] = [] # rolling buffer
        self.max_size = max_size # max size of buffer (basically the max number of interactions)

    def add(self, item):
        # if buffer is full, remove oldest item
        if len(self.buffer) >= self.max_size:
            self.buffer.pop(0)
        self.buffer.append(item)

    def retrieve(self, query: str = None, top_k: int = 5) -> List[Any]:
        if not query:
            return self.buffer[-top_k:]
            
        return [item for item in self.buffer 
                if query.lower() in str(item).lower()][-top_k:]
    
    def clear(self):
        self.buffuer = []
        
    def __len__(self):
        return len(self.buffer)

    def __repr__(self):
        return f"ShortTermMemory({len(self)} items)"
