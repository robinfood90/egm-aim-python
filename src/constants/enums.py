from enum import Enum

# class FileType(str, Enum):
#     PDF = "pdf"
#     XML = "xml"
#     IMAGE = "image"
#     CSV = "csv"
    
class InvoiceStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    FAILED = "FAILED"
    MATCHED = "MATCHED"

class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    
    
class KeywordType(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    INGREDIENT = "INGREDIENT"

class KeywordSource(str, Enum):
    DATABASE = "DATABASE"
    EXTRACTED = "EXTRACTED"
    ADDED = "ADDED"
    
class MatchType(str, Enum):
    EXACT = "EXACT"
    FUZZY = "FUZZY"
    MANUAL = "MANUAL"
    NONE = "NONE"

class ExtractionStatus(str, Enum):
    RAW="RAW"
    NORMALIZED="NORMALIZED"
    MATCHED = "MATCHED"
    CATEGORIZED = "CATEGORIZED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNMATCHED = "UNMATCHED"

class MatchThreshold:
    EXACT = 1.0
    AUTO_MATCH = 0.8  # >= 0.8 then consider as AUTO_MATCH
    REVIEW = 0.6      # >= 0.6 and < 0.8 then consider as REVIEW
    NONE = 0.0        # Below 0.6 then consider as UNMATCHED