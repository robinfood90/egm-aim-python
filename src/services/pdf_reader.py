import os
from pypdf.errors import PdfReadError
from pypdf import PdfReader
from src.schemas.file import FileReadResponse
from src.utils.file_helpers import create_error_response, create_success_response
from src.services.validate_invoice_template import validate_invoice_template
from src.constants.invoice_template import InvoiceTemplate

def read_pdf_file(
    file_path: str,
    is_extract_all: bool = False,
    is_check_invoice_template: bool = False,
) -> FileReadResponse:
    """
    Read a PDF file.
    Check invoice template if is_check_invoice_template is True.
    Extracts text from all pages if is_extract_all is True.
    """
    if not os.path.exists(file_path):
        return create_error_response(file_path=file_path, message="File not found!")

    try:
        reader = PdfReader(file_path)
        pages = reader.pages
        if not reader.pages:
            return create_error_response(file_path=file_path, message="PDF is empty")

        first_page_text = pages[0].extract_text() or ""
        # first_line = (
        #         first_page_text.split("\n")[0].strip() if first_page_text else ""
        #     )

        invoice_template_type = InvoiceTemplate.UNKNOWN
        if is_check_invoice_template:
            invoice_template_type = validate_invoice_template(first_page_text)
            if not invoice_template_type:
                return create_error_response(
                    file_path=file_path, message=f"Unknown Template"
                )

        full_text = None
        if is_extract_all:
            full_text = "\n".join(page.extract_text() or "" for page in pages).strip()

        return create_success_response(
            file_path=file_path,
            page_count=len(pages),
            # first_line=first_line,
            full_text=full_text,
            invoice_template=invoice_template_type,
        )

    except PdfReadError as e:
        return create_error_response(
            file_path=file_path, message=f"PDF read error: {e}"
        )
    except Exception as e:
        return create_error_response(
            file_path=file_path, message=f"Unexpected error: {e}"
        )
