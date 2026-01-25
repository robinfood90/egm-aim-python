from src.db.config import get_db_connection
from typing import List
from src.schemas.category_dictionary import CategoryDictionary

def get_all_active_dictionary_rules() -> List[CategoryDictionary]:
    """
    Query all active category dictionary rules for scoring logic.
    Returns a list of CategoryDictionary objects, or an empty list if not found.
    """
    conn = get_db_connection()
    if conn is None: 
        return []
    
    try:
        with conn.cursor() as cur:
            query = "SELECT * FROM category_dictionary WHERE is_active = TRUE"
            cur.execute(query)
            rows = cur.fetchall()
            
            if rows:
                return [CategoryDictionary.model_validate(row) for row in rows]
            
            return []
    except Exception as e:
        print(f"Error querying category dictionary: {e}")
        return []
    finally:
        conn.close()