from typing import List
from src.db.config import get_db_connection
from src.schemas.product_extract import ProductExtract, ProductExtractMatching
def save_extracted_products(products: List[ProductExtract], conn=None) -> List[ProductExtract]:
    is_local_conn = False
    if conn is None:
        conn = get_db_connection(autocommit=False)
        is_local_conn = True
        if conn is None:
            return []

    query = """
        INSERT INTO products_extract (
            invoice_id,
            product_code,
            raw_product_name, 
            normalized_product_name,
            quantity,
            cost_price, 
            currency,
            extraction_status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    
    params_list = [
        (
            p.invoice_id, p.product_code, p.raw_product_name,
            p.normalized_product_name, p.quantity, p.cost_price, 
            p.currency, p.extraction_status.value,
        ) for p in products
    ]

    try:
        with conn.cursor() as cur:
            cur.executemany(query, params_list, returning=True)
            
            all_ids = []
            while True:
                result = cur.fetchone()
                if result:
                    all_ids.append(result['id'])
                if not cur.nextset():
                    break
                
            for p, p_id in zip(products, all_ids):
                p.id = p_id
        
        if is_local_conn: conn.commit()
        return products
    except Exception as e:
        print(f"❌ Error saving extracted products: {repr(e)}")
        if is_local_conn: conn.rollback()
        return []
    finally:
        if is_local_conn: conn.close()


def save_matching(matching_data: List[ProductExtractMatching], conn=None) -> bool:
    """
    Updates the products_extract table with normalization, categorization and matching results.
    """
    is_local_conn = False
    if conn is None:
        conn = get_db_connection(autocommit=False)
        is_local_conn = True
        if conn is None:
            return False

    query = """
        UPDATE products_extract
        SET 
            main_category = %s,
            main_ratio = %s,
            second_category = %s,
            second_ratio = %s,
            third_category = %s,
            third_ratio = %s,
            
            matched_product_id = %s,
            match_type = %s,
            confidence = %s,
            match_reason = %s,
            normalized_product_name = %s,
            
            extraction_status = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """

    try:
        with conn.cursor() as cur:
            data = []
            for m in matching_data:
                data.append((
                    # Categorization
                    m.main_category,
                    m.main_ratio,
                    m.second_category,
                    m.second_ratio,
                    m.third_category,
                    m.third_ratio,
                    
                    # Matching
                    m.matched_product_id,
                    m.match_type.value,
                    m.confidence,
                    m.match_reason,
                    
                    # Normalization
                    m.normalized_product_name,
                    
                    m.extraction_status.value,
                    m.id
                ))
            cur.executemany(query, data)
        if is_local_conn: conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating normalization & categorization & matching: {e}")
        if is_local_conn: conn.rollback()
        return False
    finally:
        if is_local_conn: conn.close()