from src.db.config import get_db_connection
from src.schemas.product_category import ProductCategory
from src.schemas.product import ProductBase
import uuid
from typing import List

def bulk_save_product_categories(results: List[ProductCategory]) -> bool:
    """
    Bulk save product category results into the database.
    """
    conn = get_db_connection()
    if conn is None: 
        return False
    
    values = [
        (
            str(uuid.uuid4()), 
            str(r.product_id),
            r.main_category,
            r.main_ratio,
            r.second_category if r.second_category else None,
            r.second_ratio if r.second_ratio and r.second_ratio > 0 else None,
            r.third_category if r.third_category else None,
            r.third_ratio if r.third_ratio and r.third_ratio > 0 else None
        ) for r in results
    ]

    query = """
        INSERT INTO product_category (
            id, product_id, main_category, main_ratio, 
            second_category, second_ratio, third_category, third_ratio
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_id) 
        DO UPDATE SET 
            main_category = EXCLUDED.main_category,
            main_ratio = EXCLUDED.main_ratio,
            second_category = EXCLUDED.second_category,
            second_ratio = EXCLUDED.second_ratio,
            third_category = EXCLUDED.third_category,
            third_ratio = EXCLUDED.third_ratio,
            updated_at = CURRENT_TIMESTAMP
    """
    
    try:
        with conn.cursor() as cur:
            cur.executemany(query, values)
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error in bulk save: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()