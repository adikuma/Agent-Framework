from openai import OpenAI
from typing import List, Dict
from base_provider import BaseProvider

class OpenAIProvider(BaseProvider):
    def __init__(self, model="gpt-3.5-turbo", api_key=None):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, messages: List[Dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content