from pydantic import BaseModel, ConfigDict, Field
from src.constants.enums import InvoiceStatus
from datetime import datetime
from uuid import UUID
from typing import Optional

class InvoiceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: UUID
    original_file_name: str
    file_type: str
    file_size: int = Field(..., description="File size in bytes")
    invoice_url: str
    status: InvoiceStatus = InvoiceStatus.PENDING
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None