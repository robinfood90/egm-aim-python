from src.schemas.product_extract import ProductExtract
from typing import List
from src.constants.invoice_template import TEMPLATE_CONFIGS, InvoiceTemplate
import re
from uuid import UUID

def extract_products_from_text(
    full_text: str, 
    invoice_template: InvoiceTemplate, 
    invoice_id: UUID
) -> List[ProductExtract]:
    """
    Extract products from the given full text based on the invoice template.
    1. Use regex patterns defined in TEMPLATE_CONFIGS to find products.
    2. Create ProductExtract objects for each matched product line.
    """
    products: List[ProductExtract] = []
    
    config = TEMPLATE_CONFIGS.get(invoice_template)
    if not config:
        print(f"⚠️ No configuration found for template: {invoice_template}")
        return products
    
    pattern = config.get("pattern")
    if not pattern:
        print(f"⚠️ No regex pattern defined for template: {invoice_template}")
        return products
    
    matches = re.finditer(pattern, full_text, flags=re.MULTILINE)
    currency = config.get("currency", "AUD")
    
    for match in matches:
        try:
            group_dict = match.groupdict()
            raw_name = group_dict.get('desc', '').strip()
            
            product = ProductExtract(
                invoice_id=invoice_id,
                raw_product_name=raw_name,
                product_code=group_dict.get('code'),
                quantity=float(group_dict.get('qty', 0)),
                cost_price=float(group_dict.get('price', 0)),
                currency=currency,
            )
            products.append(product)
        except (ValueError, KeyError) as e:
            print(f"❌ Error extracting products: {e}")
            continue
    
    return products