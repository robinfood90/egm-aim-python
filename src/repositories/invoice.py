from src.db.config import get_db_connection
from src.constants.enums import InvoiceStatus
from src.schemas.invoice import InvoiceBase
from typing import Optional
from uuid import UUID

def get_oldest_pending_invoice() -> Optional[InvoiceBase]:
    """
    Get the first invoice with 'pending' status and oldest (oldest) creation date.
    """
    conn = get_db_connection()
    if conn is None:
        return None
        
    try:
        with conn.cursor() as cur:
            query = """
                SELECT * FROM invoice 
                WHERE status = %s 
                ORDER BY created_at ASC 
                LIMIT 1
            """
            cur.execute(query, (InvoiceStatus.PENDING.value,))
            row = cur.fetchone()
            if row:
                return InvoiceBase.model_validate(row)
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()

def update_invoice_status(invoice_id: UUID, status: InvoiceStatus, error_message: str | None = None) -> bool:
    conn = get_db_connection()
    if conn is None: return False
    
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE invoice SET status = %s, error_message = %s, updated_at = NOW() WHERE invoice_id = %s",
                    (status.value, error_message, invoice_id)
                )
        return True
    except Exception as e:
        print(f"❌ Error updating invoice status: {e}")
        return False
    finally:
        conn.close()