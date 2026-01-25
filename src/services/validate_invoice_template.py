from src.constants.invoice_template import TEMPLATE_CONFIGS, InvoiceTemplate
from typing import Optional

def validate_invoice_template(text_content: str) -> Optional[InvoiceTemplate]:
    """
    Check the text content of the PDF page to determine the type of template.
    Returns:
        str: GULLI / MAYERS / UNKNOWN
    """
    if not text_content:
        return InvoiceTemplate.UNKNOWN

    content_lower = text_content.lower()

    for template_name, config in TEMPLATE_CONFIGS.items():
        keywords = [kw.lower() for kw in config["keywords"]]
        matched_keywords = [kw for kw in keywords if kw in content_lower]
        
        # Set a threshold (match at least 2 keywords).
        if len(matched_keywords) >= 2:
            headers = [h.lower() for h in config["table_headers"]]
            matched_headers = [h for h in headers if h in content_lower]
            # Set a threshold (match at least 3 col).
            if len(matched_headers) >= 3:
                return InvoiceTemplate(template_name)
                
    return InvoiceTemplate.UNKNOWN