from typing import List
from src.db.config import get_db_connection
from src.schemas.match_candidate import MatchCandidateCreate

def save_match_candidates(candidates: List[MatchCandidateCreate]) -> bool:
    """
    Save a list of match candidates into the database.
    Returns True if success, False otherwise.
    """
    conn = get_db_connection()
    if conn is None:
        return False

    query = """
        INSERT INTO match_candidate (
            product_id,
            products_extract_id,
            confidence,
            match_type,
            match_reason
        ) VALUES (%s, %s, %s, %s, %s)
    """

    try:
        with conn.cursor() as cursor:
            data_to_insert = [
                (
                    c.product_id,
                    c.products_extract_id,
                    c.confidence,
                    c.match_type.value,
                    c.match_reason
                )
                for c in candidates
            ]
            
            cursor.executemany(query, data_to_insert)
            
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error saving match candidates: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()