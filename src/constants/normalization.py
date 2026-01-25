UNIT_MAPPING = {
    r'\b(kilograms?|kgs?|kg)\b': 'kg',
    r'\b(grams?|grs?|g)\b': 'g',
    r'\b(pieces?|pcs?|pc)\b': 'pcs',
    r'\b(milliliters?|ml)\b': 'ml',
    r'\b(liters?|l|litres?)\b': 'l',
    r'\b(bottles?|btls?)\b': 'bottle',
    r'\b(packs?|pkgs?|pk)\b': 'pack',
}

NON_MEANINGFUL_WORDS = [
    r'\bmodel\b', r'\bsize\b', r'\btype\b',
    r'\bpromo(tion)?\b', r'\bdiscount\b', r'\bfree\b', r'\bgift\b',
    r'\bvat\b', r'\btax\b', r'\bwith\b', r'\band\b', r'\bfor\b'
]

# Includes: - / _ , . * ( ) [ ] { } + | & ! # : ; @ ^
SPECIAL_CHARS_PATTERN = r'[-/_,\.\*\(\)\[\]\{\}\+\|&!#:;@\^]'