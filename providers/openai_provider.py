from pydantic import BaseModel
from typing import Any, Dict, List
from openai import OpenAI

class OpenAIProvider(BaseModel):
    model: str = "gpt-3.5-turbo"
    api_key: str = ""
    temperature: float = 0.0
    max_tokens: int = 100
    client: Any = None

    def __init__(self, **data):
        super().__init__(**data)
        self.client = OpenAI(api_key=self.api_key)
        
    def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content
