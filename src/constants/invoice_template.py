from enum import Enum

class InvoiceTemplate(str, Enum):
    GULLI = "GULLI"
    MAYERS = "MAYERS"
    UNKNOWN = "UNKNOWN"

TEMPLATE_CONFIGS = {
    InvoiceTemplate.GULLI: {
        "keywords": [
            "Gulli Food Distributors Pty Ltd", 
            "34 662 338 123",
            "orders@gullifood.com.au"
        ],
        "table_headers": [
            "PRODUCT CODE", "DESCRIPTION", "QUANTITY", 
            "UNIT PRICE", "DISC.%", "GST", "AMOUNT"
        ],
        "currency": "AUD",
        "pattern": r"^\s*(?P<code>\S+)\s+(?P<desc>.+?)\s+(?P<qty>[\d,.]+)\s+(?P<uom>Box|kg|each|unit|Unit)\s+(?P<price>[\d,.]+)"
    },
    InvoiceTemplate.MAYERS: {
        "keywords": [
            "Arla Foods Mayer Australiar", 
            "78167620706", 
            "mayers.com.au"
        ],
        "table_headers": [
            "Ordere", "Picked", "Item Code", "Item Description", 
            "Shipped Qty", "Unit Price", "Disc", "CD", "Net Price", "Line Total"
        ],
        "currency": "AUD",
        "pattern": r"^\s*(?P<ordered>\d+)\s+(?P<picked>\S+)\s+(?P<code>\S+)\s+(?P<desc>.+?)\s+(?P<qty>[\d,.]+)\s+(?P<uom>CTN|KG|EACH|PKT|UNIT|ctn|kg)\s+(?P<price>[\d,.]+)(?:.+?)\s+(?P<amount>[\d,.]+)$"
    }
}