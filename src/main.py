from src.services.pdf_reader import read_pdf_file
from src.services.extract_product import extract_products_from_text
from src.services.matching import run_matching_process
from src.repositories.invoice import get_oldest_pending_invoice, update_invoice_status
from src.repositories.product_extract import save_extracted_products, save_matching
from src.repositories.category_dictionary import get_all_active_dictionary_rules
from src.repositories.match_candidate import save_match_candidates
from src.repositories.name_keyword import save_name_keywords
from src.constants.enums import InvoiceStatus
from src.utils.display import print_extracted_products, print_matching_results, print_match_candidates
from src.schemas.invoice import InvoiceBase
from src.db.config import get_db_connection, get_listen_connection
import os
import time

CHANNEL = "invoice_inserted"

def process_queue(conn):
    """
    Get and process the invoices one by one.
    """
    print("🔍 [Worker] Checking for pending invoices...")
    while True:
        # Get oldest pending invoice
        invoice = get_oldest_pending_invoice(conn=conn)
        if not invoice:
            print("🏁 [Worker] All pending invoices processed.")
            break
        
        execute_core_logic(invoice, conn)
        
def execute_core_logic(invoice: InvoiceBase, conn):
    """
    Execute core logic for a given invoice.
    1. Read file
    2. Extract products from text & save extracted products
    3. Run matching process & save matching results
    """
    try: 
        print(f"🚀 [Worker] Processing Invoice ID: {invoice.invoice_id}")
        
        # 1. Read file
        update_invoice_status(invoice.invoice_id, InvoiceStatus.PROCESSING, conn=conn)
        conn.commit()
        
        base_url = os.getenv("BASE_URL")
        if not base_url:
            print("❌ BASE_URL not set in environment variables")
            return
        full_url = base_url + str(invoice.invoice_url)
        
        read_file = read_pdf_file(
            full_url,
            is_extract_all=True,
            is_check_invoice_template=True,
        )
        
        if not (read_file.success and read_file.full_text and read_file.invoice_template):
            raise Exception(f"Read File Failed: {read_file.error_message}")
        
        # 2. Extract products from text & save extracted products
        raw_products = extract_products_from_text(
            full_text=read_file.full_text,
            invoice_template=read_file.invoice_template,
            invoice_id=invoice.invoice_id,
        )
        if not raw_products:
            raise Exception("No products extracted from the invoice")
        
        # print_extracted_products(raw_products)
        
        save_extract_products = save_extracted_products(raw_products, conn=conn)
        update_invoice_status(invoice.invoice_id, InvoiceStatus.EXTRACTED, conn=conn)
        conn.commit()
        
        print(f"✅ Extracted products")
        
        try:
            dictionary_rules = get_all_active_dictionary_rules()
            matched_results, match_candidates, all_keywords_to_save = run_matching_process(
                save_extract_products, dictionary_rules
            )
            # print_matching_results(matched_results)
            # print_match_candidates(match_candidates)
            
            if all_keywords_to_save:
                save_name_keywords(all_keywords_to_save, conn=conn)
            if matched_results:
                save_matching(matched_results, conn=conn)
            if match_candidates:
                save_match_candidates(match_candidates, conn=conn)
            
            update_invoice_status(invoice.invoice_id, InvoiceStatus.MATCHED, conn=conn)
            conn.commit()
            print(f"✅ Matching process completed")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error during matching process: {repr(e)}")
            update_invoice_status(invoice.invoice_id, InvoiceStatus.FAILED, error_message=f"Matching failed: {str(e)}", conn=conn)
            conn.commit()
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error processing invoice ID {invoice.invoice_id}: {repr(e)}")
        update_invoice_status(invoice.invoice_id, InvoiceStatus.FAILED, error_message=str(e), conn=conn)
        conn.commit()
        
        
def main_worker():
    """
    Main loop: Listen for new invoice notifications and process the queue.
    1. Establish two DB connections: one for LISTEN/NOTIFY, another for processing.
    2. Register LISTEN on the notification channel
    3. Startup Sweep: Process any pending invoices on startup
    4. Event Loop: Wait for notifications and process the queue
    5. Error Handling & Reconnection
    6. Graceful Shutdown
    """
    print("🚀 [System] Starting Automated Invoice Worker...")

    while True:
        listen_conn = None
        worker_conn = None
        try:
            # 1. Establish two DB connections
            # Use direct connection for LISTEN (port 5432) instead of pooler (port 6543)
            listen_conn = get_listen_connection()
            worker_conn = get_db_connection(autocommit=False)

            if not listen_conn or not worker_conn:
                raise Exception("Could not establish database connections")

            # 2. Register LISTEN on the notification channel
            listen_conn.execute(f"LISTEN {CHANNEL}")
            print(f"📢 [System] Listening on channel: '{CHANNEL}'")
            print(f"🆔 [System] Session PID: {listen_conn.pgconn.backend_pid}")

            # 3. Startup Sweep: Process any pending invoices on startup
            process_queue(worker_conn)

            # 4. Event Loop: Wait for notifications and process the queue
            print("⏳ [System] Waiting for notifications...")
            while True:
                try:
                    # Use notifies() with timeout to wait for notifications
                    # This is the correct way in psycopg3
                    notifies = list(listen_conn.notifies(timeout=10))
                    
                    if notifies:
                        print(f"⚡ [Event] New notify: {len(notifies)}")
                        for n in notifies:
                            print(f"   🔔 Channel: {n.channel} | Payload: {n.payload}")
                        
                        process_queue(worker_conn)
                    else:
                        # Timeout - check connection is still alive
                        listen_conn.execute("SELECT 1")
                except Exception as notify_err:
                    print(f"⚠️ [Warning] Error waiting for notification: {notify_err}")
                    # Fallback to polling if notifies() fails
                    listen_conn.execute("SELECT 1")
                    notifies = list(listen_conn.notifies())
                    if notifies:
                        print(f"⚡ [Event] New notify: {len(notifies)}")
                        for n in notifies:
                            print(f"   🔔 Channel: {n.channel} | Payload: {n.payload}")
                        process_queue(worker_conn)
                    time.sleep(1)
                
        except Exception as e:
            print(f"❌ [Error] {e}")
            print("🔄 [System] Attempting to reconnect in 5 seconds...")
            time.sleep(5)
        finally:
            if listen_conn: listen_conn.close()
            if worker_conn: worker_conn.close()

if __name__ == "__main__":
    main_worker()