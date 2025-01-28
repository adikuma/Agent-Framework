from pydantic import BaseModel, ValidationError
from typing import Dict, List, Optional, Type
import json
from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError as SchemaError

class StructuredResponse(BaseModel):
    success: bool # was the generation successful
    data: Dict # the main result
    errors: List[str] = [] # any errors

class Validation:
    @staticmethod
    def validate_json(output: str, schema: Dict) -> bool:
        try:
            data = json.loads(output)
            jsonschema_validate(instance=data, schema=schema) # use jsonschema to validate the output
            return True
        except (json.JSONDecodeError, SchemaError):
            return False

    @staticmethod
    def validate_model(data: Dict, model: Type[BaseModel]) -> Optional[BaseModel]:
        try:
            return model(**data)
        except ValidationError:
            return None
        
        