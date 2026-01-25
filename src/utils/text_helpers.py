import re
from src.constants.normalization import UNIT_MAPPING, NON_MEANINGFUL_WORDS, SPECIAL_CHARS_PATTERN

def normalize_product_name(text: str) -> str:
    if not text: return ""
    
    text = text.lower().strip()
    
    for pattern, replacement in UNIT_MAPPING.items():
        text = re.sub(pattern, replacement, text)
    
    for word_pattern in NON_MEANINGFUL_WORDS:
        text = re.sub(word_pattern, '', text)
        
    text = re.sub(SPECIAL_CHARS_PATTERN, ' ', text)
    
    return " ".join(text.split())