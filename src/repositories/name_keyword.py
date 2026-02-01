from typing import List
from src.db.config import get_db_connection
from src.schemas.name_keywords import NameKeywordCreate

def save_name_keywords(keywords: List[NameKeywordCreate], conn=None) -> bool:
    """
    Save a list of name keywords into the database.
    Returns True if success, False otherwise."""

    is_local_conn = False
    if conn is None:
        conn = get_db_connection(autocommit=False)
        is_local_conn = True
        if conn is None:
            return False

    query = """
        INSERT INTO name_keyword (
            products_extract_id,
            keyword,
            score,
            source
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (products_extract_id, keyword) 
        DO UPDATE SET 
            score = EXCLUDED.score,
            source = EXCLUDED.source;
    """
    try:
        with conn.cursor() as cursor:
            data_to_insert = [
                (
                    kw.products_extract_id,
                    kw.keyword,
                    kw.score,
                    kw.source.value if hasattr(kw.source, "value") else kw.source,
                )
                for kw in keywords
            ]
            cursor.executemany(query, data_to_insert)
        if is_local_conn:
            conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error saving name keywords: {repr(e)}")
        if is_local_conn:
            conn.rollback()
        return False
    finally:
        if is_local_conn and conn:
            conn.close()