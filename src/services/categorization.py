import uuid
from typing import List, Dict, Optional, cast
from src.schemas.name_keywords import NameKeywordCreate
from src.schemas.category_dictionary import CategoryDictionary
from src.schemas.product_category import ProductCategory
from src.constants.enums import KeywordSource
from collections import Counter

def prepare_frequency_map(dictionary_rules: List[CategoryDictionary]) -> Dict[str, int]:
    """
    Prepare a frequency map of keywords in the category dictionary
    Example Output:{ "cheese": 2, "crackers": 1, ...}
    """
    return Counter([r.keyword.lower() for r in dictionary_rules])

def get_scored_keywords(
    product_id: uuid.UUID, 
    normalized_name: str, 
    frequency_map: Dict[str, int],
    source: KeywordSource = KeywordSource.EXTRACTED
) -> List[NameKeywordCreate]:
    """
    Split tokens from normalized name and score them based on:
        Position: decrease position_score by 0.1 per position
        Dictionary Presence: if not in the dictionary: dictionary_score = 0.3 
        Frequency: if in the dictionary, low frequencies - high scores, high frequencies - low scores: dictionary_score = 1.0 / number_of_appearances_in_dict
    Final Score = position_score * dictionary_score
    0 < final_score <= 1.0
    """
    if not normalized_name:
        return []

    tokens = normalized_name.split()
    scored_keywords = []
    
    for index, token in enumerate(tokens):
        position_score = max(0.1, 1.0 - (index * 0.1))
        num_appearances = frequency_map.get(token, 0)
        dictionary_score = 0.3
        if num_appearances > 0:
            dictionary_score = 1.0 / num_appearances

        final_score = round(position_score * dictionary_score, 2)
        
        scored_keywords.append(NameKeywordCreate(
            products_extract_id=product_id,
            keyword=token,
            score=final_score,
            source=source
        ))
        
    return scored_keywords

def prepare_category_rules_map(dictionary_rules: List[CategoryDictionary]) -> Dict[str, List[Dict]]:
    """
    Group category rules by keyword for quick lookup
    Example Output:{
        "cheese": [
            {"category_code": "CAT_CHEESE", "category_name": "Cheese", "weight": 1.0},
            {"category_code": "CAT_PIZZA", "category_name": "Pizza", "weight": 0.5}
        ],...
    }
    """
    rules_map = {}
    for rule in dictionary_rules:
        kw = rule.keyword.lower()
        rules_map.setdefault(kw, []).append({
            "category_code": rule.category_code,
            "category_name": rule.category_name,
            "weight": rule.weight
        })
    return rules_map

def calculate_category_scores(
    scored_keywords: List[NameKeywordCreate], 
    category_rules_map: Dict[str, List[Dict]]
) -> Dict[str, Dict]:
    """
    Implement Keyword-to-Category Mapping
    Score = sum(keyword_score * weight)
    Example Output:{
        "CAT_CHEESE": {"category_name": "Cheese", "score": 2.5},
        "CAT_PIZZA": {"category_name": "Pizza", "score": 1.2},
        ...
    }
    """
    category_results = {}

    for sk in scored_keywords:
        keyword = sk.keyword 
        if keyword in category_rules_map:
            matching_rules = category_rules_map[keyword]
            for rule in matching_rules:
                code = rule["category_code"]
                contribution = sk.score * rule["weight"]
                if code not in category_results:
                    category_results[code] = {
                        "category_name": rule["category_name"],
                        "score": 0.0
                    }
                category_results[code]["score"] = round(
                    category_results[code]["score"] + contribution, 2
                )

    return category_results

def get_tier_info(index: int, items: list, total_score: float) -> tuple[Optional[str], Optional[float]]:
    """
    Get category code and ratio for the given tier index
    """
    if index < len(items):
        category_code, data = items[index] 
        ratio = round(data["score"] / total_score, 2) if total_score > 0 else 0.0
        return category_code, ratio
    return None, None

def select_top_categories(
    product_id: uuid.UUID,
    category_results: Dict[str, Dict]
) -> Optional[ProductCategory]:
    """
    Select top 3 categories based on scores and calculate their ratios
    """
    
    # No categories matched
    if not category_results:
        return None

    # Sort categories by score descending    
    sorted_items = sorted(
        category_results.items(), 
        key=lambda x: x[1]["score"], 
        reverse=True
    )

    # Calculate total score of all categories
    total_score = sum(item[1]["score"] for item in sorted_items)

    main_category, main_ratio = get_tier_info(0, sorted_items, total_score)
    second_category, second_ratio = get_tier_info(1, sorted_items, total_score)
    third_category, third_ratio = get_tier_info(2, sorted_items, total_score)
    
    ratios = [r for r in [main_ratio, second_ratio, third_ratio] if r is not None]
    current_total = sum(ratios)

    if current_total > 1.0:
        if third_ratio is not None:
            third_ratio = round(1.0 - (main_ratio or 0) - (second_ratio or 0), 2)
        elif second_ratio is not None:
            second_ratio = round(1.0 - (main_ratio or 0), 2)
        elif main_ratio is not None:
            main_ratio = 1.0

    return ProductCategory(
        id=uuid.uuid4(),
        product_id=product_id,
        main_category=cast(str, main_category),
        main_ratio=main_ratio if main_ratio is not None else 0.0,
        second_category=second_category,
        second_ratio=second_ratio,
        third_category=third_category,
        third_ratio=third_ratio
    )