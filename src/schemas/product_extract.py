from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from src.constants.enums import MatchType, ExtractionStatus
from uuid import UUID

class ProductExtract(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[UUID] = None
    invoice_id: UUID
    raw_product_name: str 
    normalized_product_name: Optional[str] = None
    product_code: Optional[str] = None
    barcode: Optional[str] = None
    sku: Optional[str] = None
    quantity: Optional[float] = None
    # uom: Optional[str] = Field(None, description="Unit of Measure (e.g., kg, box)")
    cost_price: Optional[float] = None
    currency: Optional[str] = None
    extraction_status: ExtractionStatus = ExtractionStatus.RAW
    
class ProductExtractCategorization(ProductExtract):
    main_category: Optional[str] = None
    main_ratio: Optional[float] = Field(None, ge=0, le=1.0)
    second_category: Optional[str] = None
    second_ratio: Optional[float] = Field(None, ge=0, le=1.0)
    third_category: Optional[str] = None
    third_ratio: Optional[float] = Field(None, ge=0, le=1.0)
    
class ProductExtractMatching(ProductExtractCategorization):
    matched_product_id: Optional[UUID] = None 
    match_type: MatchType = MatchType.NONE
    confidence: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    match_reason: Optional[str] = None