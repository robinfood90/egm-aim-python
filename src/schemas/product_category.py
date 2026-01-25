from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from uuid import UUID
from typing import Optional

class ProductCategory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: Optional[UUID] = None
    
    main_category: str
    main_ratio: float = Field(..., ge=0, le=1.0)
    
    second_category: Optional[str] = None
    second_ratio: Optional[float] = Field(0.0, ge=0, le=1.0)
    
    third_category: Optional[str] = None
    third_ratio: Optional[float] = Field(0.0, ge=0, le=1.0)
    
    # created_at: datetime
    # updated_at: datetime