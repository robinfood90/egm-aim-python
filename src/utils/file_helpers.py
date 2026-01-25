from typing import Optional
from src.schemas.file import FileReadResponse
from src.constants.invoice_template import InvoiceTemplate

def create_error_response(file_path: str, message: str) -> FileReadResponse:
    return FileReadResponse(
        file_path=str(file_path),
        success=False,
        error_message=str(message)
    )

def create_success_response(
    file_path: str, 
    page_count: int, 
    # first_line: Optional[str] = None,
    full_text: Optional[str] = None,
    invoice_template: Optional[InvoiceTemplate] = InvoiceTemplate.UNKNOWN
) -> FileReadResponse:
    return FileReadResponse(
        file_path=str(file_path),
        success=True,
        page_count=page_count,
        # first_line=first_line,
        full_text=full_text,
        invoice_template=invoice_template
    )