from pydantic import BaseModel, ConfigDict, Field
from src.constants.enums import InvoiceStatus
from datetime import datetime
from uuid import UUID
from typing import Optional
from src.constants.enums import MatchType

class MatchCandidateCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    products_extract_id: UUID
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    match_type: MatchType = MatchType.FUZZY
    match_reason: Optional[str] = None
    
    #
    extracted_product_name: Optional[str] = None
    product_name: Optional[str] = None
    