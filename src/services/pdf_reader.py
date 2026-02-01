import os
import requests
import tempfile
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from pypdf.errors import PdfReadError
from pypdf import PdfReader
from src.schemas.file import FileReadResponse
from src.utils.file_helpers import create_error_response, create_success_response
from src.services.validate_invoice_template import validate_invoice_template
from src.constants.invoice_template import InvoiceTemplate

def extract_text_with_layout(img) -> str:
    """
    Use image_to_data to get coordinates and restructure the correct line of text.
    """
    # Get coordinates x, y, width, height, text
    data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DATAFRAME)
    
    # Remove rows with NaN or empty text
    data = data[data.text.notna() & (data.text.str.strip() != "")]
    
    if data.empty:
        return ""

    # Group by 'block_num' and 'line_num' (these are the actual lines Tesseract recognizes)
    # Sort words in each line by 'left' coordinate (left to right)
    lines = []
    for _, line_df in data.groupby(['block_num', 'line_num']):
        sorted_line = line_df.sort_values('left')
        line_text = " ".join(sorted_line['text'].astype(str))
        lines.append(line_text)
        
    return "\n".join(lines)

def read_pdf_file(
    file_path: str,
    is_extract_all: bool = False,
    is_check_invoice_template: bool = False,
) -> FileReadResponse:
    """
    Read a PDF file.
    If it's a URL, downloads to a temporary file, processes it, and then deletes it.
    Handle file extraction: text, image-based (OCR), invoice template validation.
    """
    is_url = file_path.startswith(("http://", "https://"))
    target_path = file_path
    temp_pdf = None
    
    # Get Poppler path from environment variable (optional)
    # If not set, pdf2image will use system PATH
    poppler_path = os.getenv("POPPLER_PATH")

    try:
        # --- Download file if it's a URL ---
        if is_url:
            try:
                response = requests.get(file_path, timeout=30)
                response.raise_for_status()
                # Create a temporary file to save the downloaded PDF
                temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                temp_pdf.write(response.content)
                temp_pdf.close()
                target_path = temp_pdf.name
            except requests.exceptions.HTTPError as e:
                return create_error_response(
                    file_path=file_path, message=f"HTTP error: {e}"
                )
            except Exception as e:
                return create_error_response(
                    file_path=file_path, message=f"Download file error: {e}"
                )

        if not os.path.exists(target_path):
            return create_error_response(file_path=file_path, message="File not found!")

        # --- Read PDF file ---
        reader = PdfReader(target_path)
        pages = reader.pages
        if not pages:
            return create_error_response(file_path=file_path, message="PDF is empty")

        # --- Check invoice file: If the first page has no text, it might be an image-based PDF requiring OCR ---
        first_page_text = pages[0].extract_text() or ""
        full_text = None

        # first_line = (
        #         first_page_text.split("\n")[0].strip() if first_page_text else ""
        #     )

        # --- Extract text ---
        if first_page_text.strip():
            if is_extract_all:
                full_text = "\n".join(
                    page.extract_text() or "" for page in pages
                ).strip()
        
        # --- Perform OCR if no text found ---
        else:
            try:
                # Convert PDF pages to images (high DPI for better OCR accuracy - DPI=300)
                # Prepare convert_from_path arguments
                convert_kwargs = {"dpi": 300}
                if poppler_path:
                    convert_kwargs["poppler_path"] = poppler_path
                
                images = (
                    convert_from_path(target_path, **convert_kwargs)
                    if is_extract_all
                    else convert_from_path(
                        target_path, first_page=1, last_page=1, **convert_kwargs
                    )
                )
                ocr_results = []
                # Perform OCR on each image
                for i, img in enumerate(images):
                    # page_text = pytesseract.image_to_string(img, lang="eng")
                    page_text = extract_text_with_layout(img)
                    ocr_results.append(page_text)
                    if i == 0:
                        first_page_text = page_text

                full_text = "\n".join(ocr_results).strip()
            except Exception as ocr_err:
                return create_error_response(
                    file_path=file_path, message=f"OCR failed: {ocr_err}"
                )

        # --- Validate invoice template if required ---
        invoice_template_type = InvoiceTemplate.UNKNOWN
        if is_check_invoice_template:
            invoice_template_type = validate_invoice_template(first_page_text)
            if invoice_template_type == InvoiceTemplate.UNKNOWN:
                return create_error_response(
                    file_path=file_path, message="Unknown Invoice Template"
                )

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

    finally:
        # --- Cleanup temporary file if created ---
        if temp_pdf and os.path.exists(temp_pdf.name):
            try:
                os.remove(temp_pdf.name)
            except Exception as e:
                print(
                    f"⚠️ Warning: Could not delete temporary file {temp_pdf.name}: {e}"
                )
