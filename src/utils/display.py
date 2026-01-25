
from tabulate import tabulate
from typing import List
from src.schemas.product_extract import ProductExtract, ProductExtractMatching
from src.schemas.match_candidate import MatchCandidateCreate

def print_extracted_products(products: List[ProductExtract]):
    if not products:
        print("⚠️ No products extracted.")
        return
    
    headers = [
        "STT", 
        "Product Code", 
        "Description", 
        "Quantity", 
        "Unit Price", 
    ]

    table_data = []
    for i, p in enumerate(products, 1):
        table_data.append([
            i,
            p.product_code or "",
            p.raw_product_name or "",
            f"{p.quantity or 0:,.3f}",
            f"{p.cost_price or 0:,.2f}",
        ])

    print("-" * 50)
    print(tabulate(
        table_data, 
        headers=headers, 
        tablefmt="grid", 
        stralign="left", 
        numalign="right"
    ))
    
def print_matching_results(matched_products: List[ProductExtractMatching]):
    if not matched_products:
        print("⚠️ No matching results to display.")
        return
    
    headers = [
        "STT", 
        "Code", 
        "Raw Name", 
        "Normalized Name",
        "Status",
        "Match Type", 
        "Confidence",
        "DB Product ID",
        "Main Category",
        "Second Category",
        "Third Category",
        "Reason",
    ]

    table_data = []
    for i, p in enumerate(matched_products, 1):
        status_icon = "✅" if p.extraction_status.value == "MATCHED" else "⏳"
        table_data.append([
            i,
            p.product_code or "",
            p.raw_product_name or "",
            p.normalized_product_name or "",
            f"{status_icon} {p.extraction_status.value}",
            p.match_type.value,
            p.confidence,
            p.matched_product_id or "---",
            p.main_category or "",
            p.second_category or "",
            p.third_category or "",
            p.match_reason or "",
        ])

    print(f"\n📊 MATCHING PROCESS RESULT: {len(matched_products)} items")
    print("=" * 100)
    
    print(tabulate(
        table_data, 
        headers=headers, 
        tablefmt="grid", 
        stralign="left", 
        numalign="center"
    ))
    
    matched_count = sum(1 for p in matched_products if p.matched_product_id)
    print(f"\n📈 Summary: Matched {matched_count}/{len(matched_products)} products.")

def print_match_candidates(match_candidates: List[MatchCandidateCreate]):
    if not match_candidates:
        print("\nℹ️ No fuzzy candidates found for review.")
        return
    
    headers = [
        "STT", 
        "Extracted Product Name", 
        "DB Product Name (Candidate)",
        "Confidence",
        "Product Extract ID",
        "DB Product ID"
    ]

    table_data = []
    for i, c in enumerate(match_candidates, 1):
        table_data.append([
            i,
            c.extracted_product_name or "---",
            c.product_name or "---",
            c.confidence,
            c.products_extract_id,
            c.product_id
        ])

    print("-" * 120)
    print(tabulate(
        table_data, 
        headers=headers, 
        tablefmt="grid", 
        stralign="left", 
        numalign="center"
    ))
    print(f"\n🔍 FUZZY MATCH CANDIDATES: {len(match_candidates)} candidates found")
    