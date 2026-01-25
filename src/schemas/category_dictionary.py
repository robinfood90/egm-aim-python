from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from src.constants.enums import KeywordType

class CategoryDictionary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_code: str
    category_name: str
    keyword: str
    weight: float
    keyword_type: KeywordType
    is_active: bool