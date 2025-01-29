from abc import ABC, abstractmethod
from typing import List, Dict

class BaseProvider(ABC):
    @abstractmethod
    def generate(self, messages: List[Dict]) -> str:
        pass
