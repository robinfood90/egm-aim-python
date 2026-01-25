from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from src.constants.enums import ProductStatus
from uuid import UUID
from datetime import datetime

class ProductBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: Optional[str] = None
    sku: Optional[str] = None
    plu: Optional[str] = None
    product_code: Optional[str] = None
    bar_code: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    cost: Optional[float] = Field(None, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    status: ProductStatus = ProductStatus.ACTIVE
    # supplier_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
class ProductFuzzyCandidate(BaseModel):
    id: UUID
    name: str