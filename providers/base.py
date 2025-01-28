from abc import ABC, abstractmethod
from typing import Any, List

# base provider
class BaseProvider(ABC):
    @abstractmethod
    def generate_response(self, item: Any):
        pass

