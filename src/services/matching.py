from typing import List, Optional, Tuple
from rapidfuzz import process, fuzz
from src.schemas.product import ProductBase
from src.schemas.product_extract import ProductExtract, ProductExtractMatching
from src.schemas.category_dictionary import CategoryDictionary
from src.schemas.match_candidate import MatchCandidateCreate
from src.schemas.name_keywords import NameKeywordCreate
from src.constants.enums import MatchType, MatchThreshold, ExtractionStatus
from src.repositories.product import (
    get_products_by_identifiers,
    get_products_by_categories,
)
from src.utils.text_helpers import normalize_product_name
from src.services.categorization import (
    get_scored_keywords,
    prepare_frequency_map,
    prepare_category_rules_map,
    calculate_category_scores,
    select_top_categories,
)


def run_matching_process(
    extracted_products: List[ProductExtract], dictionary_rules: List[CategoryDictionary]
) -> Tuple[List[ProductExtractMatching], List[MatchCandidateCreate], List[NameKeywordCreate]]:
    """
    1. Exact Matching: by product_code, sku, barcode
    2. Fuzzy Matching: by normalized product name
    2.1 Categorization: by scored keywords
    2.2. Fuzzy Matching: by category similarity (RapidFuzz)
    """

    # Exact Matching Preparation
    codes = [p.product_code for p in extracted_products if p.product_code]
    barcodes = [p.barcode for p in extracted_products if p.barcode]
    skus = [p.sku for p in extracted_products if p.sku]

    db_products: List[ProductBase] = get_products_by_identifiers(codes, barcodes, skus)

    db_by_code = {p.product_code: p for p in db_products if p.product_code}
    db_by_barcode = {p.bar_code: p for p in db_products if p.bar_code}
    db_by_sku = {p.sku: p for p in db_products if p.sku}

    # Fuzzy Matching: Categorization Preparation
    keywords_frequency_map = prepare_frequency_map(dictionary_rules)
    category_rules_map = prepare_category_rules_map(dictionary_rules)

    matched_results: List[ProductExtractMatching] = []
    match_candidates: List[MatchCandidateCreate] = []
    all_keywords_to_save: List[NameKeywordCreate] = []

    for item in extracted_products:
        match_result = ProductExtractMatching(
            **item.model_dump(),
            matched_product_id=None,
            match_type=MatchType.NONE,
            confidence=None,
            match_reason=None,
        )
        match_result.normalized_product_name = normalize_product_name(
            item.raw_product_name
        )

        match_found: Optional[ProductBase] = None

        # 1. Exact Matching Logic
        if item.barcode and item.barcode in db_by_barcode:
            match_found = db_by_barcode[item.barcode]
            match_result.match_reason = "Exact barcode match"
        elif item.sku and item.sku in db_by_sku:
            match_found = db_by_sku[item.sku]
            match_result.match_reason = "Exact SKU match"
        elif item.product_code and item.product_code in db_by_code:
            match_found = db_by_code[item.product_code]
            match_result.match_reason = "Exact product code match"

        if match_found:
            match_result.matched_product_id = match_found.id
            match_result.match_type = MatchType.EXACT
            match_result.confidence = 1.0
            match_result.extraction_status = ExtractionStatus.MATCHED

        # 2. Fuzzy Matching Logic
        else:
            match_result.extraction_status = ExtractionStatus.NORMALIZED

            # 2.1 Categorization
            product_extract_id = item.id
            scored_keywords = get_scored_keywords(
                product_extract_id,
                match_result.normalized_product_name,
                keywords_frequency_map,
            )
            high_score_keywords = sorted(
                [kw for kw in scored_keywords if kw.score > 0.3],
                key=lambda x: x.score,
                reverse=True,
            )[:3]
            category_results = calculate_category_scores(
                scored_keywords, category_rules_map
            )
            top_cates = select_top_categories(product_extract_id, category_results)

            if high_score_keywords:
                all_keywords_to_save.extend(high_score_keywords)

            if top_cates and top_cates.main_category:
                match_result.main_category = top_cates.main_category
                match_result.main_ratio = top_cates.main_ratio
                match_result.second_category = top_cates.second_category
                match_result.second_ratio = top_cates.second_ratio
                match_result.third_category = top_cates.third_category
                match_result.third_ratio = top_cates.third_ratio
                match_result.extraction_status = ExtractionStatus.CATEGORIZED

                # 2.2 Fuzzy Matching by Category Similarity
                search_categories = [
                    match_result.main_category,
                    match_result.second_category,
                    match_result.third_category,
                ]
                products_from_categories = get_products_by_categories(search_categories)

                if products_from_categories:
                    norm_db_map = {
                        normalize_product_name(p.name): p
                        for p in products_from_categories
                    }
                    choices = list(norm_db_map.keys())

                    # RapidFuzz: Get all restults with score >= 60 (0.6 or 60%)
                    score_cutoff_pct = int(MatchThreshold.REVIEW * 100)
                    fuzzy_results = process.extract(
                        match_result.normalized_product_name,
                        choices,
                        scorer=fuzz.token_set_ratio,
                        score_cutoff=score_cutoff_pct,
                        limit=None,
                    )

                    if fuzzy_results:
                        # Match candidates for review
                        current_item_candidates = [
                            MatchCandidateCreate(
                                products_extract_id=product_extract_id,
                                product_id=norm_db_map[res[0]].id,
                                confidence=round(res[1] / 100, 2),
                                match_type=MatchType.FUZZY,
                                match_reason=(
                                    "Fuzzy match by name & category"
                                    if i == 0 and (res[1] / 100) >= MatchThreshold.AUTO_MATCH
                                    else "High similarity, needs human check"
                                ),
                                # For test, not saved to DB
                                extracted_product_name=match_result.raw_product_name,
                                product_name=norm_db_map[res[0]].name,
                            )
                            for i, res in enumerate(fuzzy_results)
                        ]
                        match_candidates.extend(current_item_candidates)

                        # Take the best match
                        best_name, best_score, _ = fuzzy_results[0]
                        best_db_prod = norm_db_map[best_name]
                        best_confidence = round(best_score / 100, 2)

                        if (best_score / 100) >= MatchThreshold.AUTO_MATCH:
                            match_result.matched_product_id = best_db_prod.id
                            match_result.match_type = MatchType.FUZZY
                            match_result.confidence = best_confidence
                            match_result.extraction_status = ExtractionStatus.MATCHED
                            match_result.match_reason = "Fuzzy match by name & category"
                        else:
                            match_result.extraction_status = (
                                ExtractionStatus.REVIEW_REQUIRED
                            )
                            match_result.match_type = MatchType.FUZZY
                            match_result.confidence = best_confidence
                            match_result.match_reason = (
                                "High similarity, needs human check"
                            )
                    else:
                        match_result.extraction_status = ExtractionStatus.CATEGORIZED
                        match_result.match_reason = "Categorized but no products matched > 60%"
            else:
                
                match_result.extraction_status = ExtractionStatus.UNMATCHED
                match_result.match_reason = "No exact match and could not categorize"

        matched_results.append(match_result)

    return matched_results, match_candidates, all_keywords_to_save