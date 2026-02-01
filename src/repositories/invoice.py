from src.db.config import get_db_connection
from src.constants.enums import InvoiceStatus
from src.schemas.invoice import InvoiceBase
from typing import Optional
from uuid import UUID

def get_oldest_pending_invoice(conn=None) -> Optional[InvoiceBase]:
    is_local_conn = False
    if conn is None:
        conn = get_db_connection(autocommit=False)
        is_local_conn = True
        if conn is None:
            return None
        
    try:
        with conn.cursor() as cur:
            # Using FOR UPDATE SKIP LOCKED to avoid race conditions
            query = """
                SELECT * FROM invoice 
                WHERE status = %s 
                ORDER BY created_at ASC 
                LIMIT 1
                FOR UPDATE SKIP LOCKED
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
        if is_local_conn and conn:
            conn.close()

def update_invoice_status(invoice_id: UUID, status: InvoiceStatus, error_message: str | None = None, conn=None) -> bool:
    is_local_conn = False
    if conn is None:
        conn = get_db_connection(autocommit=False)
        is_local_conn = True
        if conn is None: 
            return False
    
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE invoice SET status = %s, error_message = %s, updated_at = NOW() WHERE invoice_id = %s",
                (status.value, error_message, invoice_id)
            )
    
        if is_local_conn:
            conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error updating invoice status: {e}")
        if is_local_conn: conn.rollback()
        return False
    finally:
        if is_local_conn:
            conn.close()