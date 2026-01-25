import asyncio
from typing import List, Dict
from src.repositories.product import get_all_products
from src.repositories.category_dictionary import get_all_active_dictionary_rules
from src.repositories.product_category import bulk_save_product_categories
from src.schemas.product_category import ProductCategory
from src.services.categorization import (
    prepare_frequency_map,
    get_scored_keywords,
    prepare_category_rules_map,
    calculate_category_scores,
    select_top_categories
)
from src.constants.enums import KeywordSource
from src.utils.text_helpers import normalize_product_name

def categorize_single_product(
    product,
    frequency_map: Dict[str, int], 
    category_rules_map: Dict[str, List[Dict]]
) -> ProductCategory | None:
    """
    Categorize a single product based on its name
    """
    scored_keywords = get_scored_keywords(
        product_id=product.id,
        normalized_name=normalize_product_name(product.name),
        frequency_map=frequency_map,
        source=KeywordSource.DATABASE
    )

    category_results = calculate_category_scores(
        scored_keywords=scored_keywords,
        category_rules_map=category_rules_map
    )

    top_cate = select_top_categories(
        product_id=product.id,
        category_results=category_results
    )
    return top_cate

async def run_master_categorization(dictionary_rules: List):
    """
    Run categorization for all products in the master product database
    """
    freq_map = prepare_frequency_map(dictionary_rules)
    rules_map = prepare_category_rules_map(dictionary_rules)

    all_products = get_all_products()
    final_results = []
    
    for index, product in enumerate(all_products):
        result = categorize_single_product(product, freq_map, rules_map)
        if result:
            final_results.append(result)

    return final_results

async def main():
    # Get active category dictionary rules
    dictionary_rules = get_all_active_dictionary_rules()
    
    if not dictionary_rules:
        print("No active dictionary rules found.")
        return

    # Run master categorization
    results = await run_master_categorization(dictionary_rules)
 
    # Save results to DB
    if results:
        print(f"[INFO] Starting to save {len(results)} results...")
        success = bulk_save_product_categories(results)
        
        if success:
            print("[FINISH] The system is now ready with the new categorization data.")
        else:
            print("[FAIL] Data saving failed.")

if __name__ == "__main__":
    asyncio.run(main())