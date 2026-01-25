from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from src.constants.enums import KeywordSource
from datetime import datetime

class NameKeywordCreate(BaseModel):
    keyword: str = Field(..., min_length=1)
    score: float = Field(..., ge=0, le=1.0)
    source: KeywordSource
    products_extract_id: UUID

class NameKeyword(NameKeywordCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime