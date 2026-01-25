from pydantic import BaseModel, ConfigDict
from typing import Optional
from src.constants.invoice_template import InvoiceTemplate

class FileReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_path: str
    success: bool
    page_count: Optional[int] = None
    # first_line: Optional[str] = None
    full_text: Optional[str] = None
    error_message: Optional[str] = None
    invoice_template: Optional[InvoiceTemplate] = InvoiceTemplate.UNKNOWN