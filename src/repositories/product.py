from src.db.config import get_db_connection
from typing import List
from src.schemas.product import ProductBase, ProductFuzzyCandidate

def get_all_products() -> List[ProductBase]:
    """
    Retrieve all products from the database."""
    products = []
    conn = get_db_connection()
    if conn is None: return products
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM product")
            rows = cur.fetchall()
            
            for row in rows:
                products.append(ProductBase.model_validate(row))   
    except Exception as e:
        print(f"Error retrieving products: {e}")
    finally:
        conn.close()
    return products

def get_products_by_identifiers(
    codes: List[str], 
    barcodes: List[str], 
    skus: List[str]
) -> List[ProductBase]:
    """
    Query products based on product_code, barcode, or sku.
    """
    conn = get_db_connection()
    if conn is None:
        return []
    
    products = []
    try:
        with conn.cursor() as cur:
            query = """
                SELECT * FROM product 
                WHERE product_code = ANY(%s) 
                   OR bar_code = ANY(%s) 
                   OR sku = ANY(%s)
            """
            cur.execute(query, (codes, barcodes, skus))
            rows = cur.fetchall()
            
            for row in rows:
                products.append(ProductBase.model_validate(row))
                
    except Exception as e:
        print(f"Error querying products: {e}")
    finally:
        conn.close()
        
    return products


def get_products_by_categories(search_categories: List[str]) -> List[ProductFuzzyCandidate]:
    """
    Query products that belong to any of the specified categories.
    """
    conn = get_db_connection()
    if conn is None:
        return []

    query = """
        SELECT DISTINCT p.id, p.name
        FROM product p
        JOIN product_category pc ON p.id = pc.product_id
        WHERE pc.main_category = ANY(%s)
           OR pc.second_category = ANY(%s)
           OR pc.third_category = ANY(%s)
    """
    
    products = []
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (search_categories, search_categories, search_categories))
            rows = cursor.fetchall()
            for row in rows:
                products.append(ProductFuzzyCandidate.model_validate(row))
    except Exception as e:
        print(f"Error fetching products by categories: {e}")
    finally:
        conn.close()
        
    return products