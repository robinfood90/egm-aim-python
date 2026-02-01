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
from src.db.supabase_client import get_supabase_client
import os
import time

CHANNEL = "invoice_inserted"

def process_queue(conn):
    """
    Get and process the invoices one by one.
    Returns True if invoices were processed, False if queue was empty.
    """
    invoice = get_oldest_pending_invoice(conn=conn)
    if not invoice:
        return False
    
    print("🔍 [Worker] Checking for pending invoices...")
    processed_count = 0
    while True:
        # Get oldest pending invoice
        invoice = get_oldest_pending_invoice(conn=conn)
        if not invoice:
            if processed_count > 0:
                print(f"🏁 [Worker] Processed {processed_count} invoice(s). Queue is now empty.")
            break
        
        execute_core_logic(invoice, conn)
        processed_count += 1
    
    return processed_count > 0
        
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
        
        
def main_worker(mode="realtime", poll_interval=5):
    """
    Main loop: Listen for new invoice notifications and process the queue.
    
    Args:
        mode: "realtime" (Supabase Realtime), "listen" (LISTEN/NOTIFY), or "polling"
        poll_interval: Polling interval in seconds (only used if mode="polling")
    
    1. Establish DB connection(s)
    2. Register subscription/listen based on mode
    3. Startup Sweep: Process any pending invoices on startup
    4. Event Loop: Wait for notifications (or poll) and process the queue
    5. Error Handling & Reconnection
    6. Graceful Shutdown
    """
    print("🚀 [System] Starting Automated Invoice Worker...")
    print(f"📋 [Config] Mode: {mode.title()}")

    while True:
        listen_conn = None
        worker_conn = None
        supabase_client = None
        subscription = None
        
        try:
            # 1. Establish DB connections
            worker_conn = get_db_connection(autocommit=False)
            if not worker_conn:
                raise Exception("Could not establish worker database connection")

            # 2. Setup based on mode
            if mode == "realtime":
                # Try Supabase Realtime
                supabase_client = get_supabase_client()
                if not supabase_client:
                    print("⚠️ [Warning] Supabase Realtime not available, falling back to polling")
                    mode = "polling"
            
            elif mode == "listen":
                # Try LISTEN/NOTIFY
                listen_conn = get_listen_connection()
                if not listen_conn:
                    print("⚠️ [Warning] Could not establish LISTEN connection, falling back to polling")
                    mode = "polling"

            # 3. Register subscription/listen based on mode
            if mode == "realtime" and supabase_client:
                try:
                    # Subscribe to INSERT events on invoice table using postgres_changes
                    print(f"📢 [Realtime] Subscribing to invoice table INSERT events...")
                    
                    # Create callback that has access to worker_conn
                    def on_insert(payload):
                        try:
                            # Payload structure for postgres_changes
                            event_type = payload.get("eventType") or payload.get("type")
                            new_record = payload.get("new", {}) or payload.get("record", {})
                            
                            if event_type == "INSERT" and new_record.get("status") == "PENDING":
                                invoice_id = new_record.get("invoice_id")
                                print(f"⚡ [Realtime] New invoice INSERT: {invoice_id}")
                                print(f"   📦 Payload: {payload}")
                                # Process queue to handle this invoice
                                process_queue(worker_conn)
                        except Exception as e:
                            print(f"⚠️ [Realtime] Error in callback: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # Use channel().on('postgres_changes', ...) API
                    subscription = supabase_client.channel('invoice-changes').on(
                        'postgres_changes',
                        {
                            'event': 'INSERT',
                            'schema': 'public',
                            'table': 'invoice',
                            'filter': 'status=eq.PENDING'  # Filter for PENDING status
                        },
                        on_insert
                    ).subscribe()
                    
                    print(f"✅ [Realtime] Subscription active")
                except Exception as realtime_err:
                    print(f"⚠️ [Warning] Failed to subscribe to Realtime: {realtime_err}")
                    import traceback
                    traceback.print_exc()
                    print("   Falling back to polling mode...")
                    mode = "polling"
                    if subscription:
                        try:
                            subscription.unsubscribe()
                        except:
                            pass
                        subscription = None
            
            elif mode == "listen" and listen_conn:
                try:
                    listen_conn.execute(f"LISTEN {CHANNEL}")
                    print(f"📢 [System] Listening on channel: '{CHANNEL}'")
                    print(f"🆔 [System] Session PID: {listen_conn.pgconn.backend_pid}")
                except Exception as listen_err:
                    print(f"⚠️ [Warning] Failed to register LISTEN: {listen_err}")
                    print("   Falling back to polling mode...")
                    use_listen_notify = False
                    if listen_conn:
                        listen_conn.close()
                        listen_conn = None

            # 4. Startup Sweep: Process any pending invoices on startup
            process_queue(worker_conn)

            # 5. Event Loop: Wait for notifications or poll
            if mode == "realtime" and subscription:
                # Supabase Realtime mode - events are handled by callback
                print("⏳ [Realtime] Waiting for invoice INSERT events...")
                print("   (Press Ctrl+C to stop)")
                try:
                    # Keep the subscription alive and process any missed invoices periodically
                    poll_count = 0
                    while True:
                        time.sleep(1)
                        poll_count += 1
                        # Process any pending invoices that might have been missed every 30 seconds
                        if poll_count % 30 == 0:
                            print(f"💓 [Realtime] Heartbeat - checking for missed invoices...")
                            process_queue(worker_conn)
                except KeyboardInterrupt:
                    print("\n🛑 [Realtime] Stopping...")
                    try:
                        subscription.unsubscribe()
                    except:
                        pass
                    break
                except Exception as realtime_loop_err:
                    print(f"⚠️ [Warning] Error in Realtime loop: {realtime_loop_err}")
                    import traceback
                    traceback.print_exc()
                    print("   Falling back to polling mode...")
                    mode = "polling"
            
            elif mode == "listen" and listen_conn:
                try:
                    listen_conn.execute(f"LISTEN {CHANNEL}")
                    print(f"📢 [System] Listening on channel: '{CHANNEL}'")
                    print(f"🆔 [System] Session PID: {listen_conn.pgconn.backend_pid}")
                except Exception as listen_err:
                    print(f"⚠️ [Warning] Failed to register LISTEN: {listen_err}")
                    print("   Falling back to polling mode...")
                    mode = "polling"
                    if listen_conn:
                        listen_conn.close()
                        listen_conn = None
                
                if mode == "listen":
                    print("⏳ [System] Waiting for notifications...")
                    poll_count = 0
                    while True:
                        try:
                            # Poll for notifications by executing a query
                            listen_conn.execute("SELECT 1")
                            
                            # Check for notifications
                            notifies = list(listen_conn.notifies())
                            
                            if notifies:
                                print(f"⚡ [Event] New notify: {len(notifies)}")
                                for n in notifies:
                                    print(f"   🔔 Channel: {n.channel} | Payload: {n.payload}")
                                
                                process_queue(worker_conn)
                                poll_count = 0
                            else:
                                poll_count += 1
                                if poll_count % 30 == 0:
                                    print(f"💓 [Heartbeat] Still listening... (poll #{poll_count})")
                                time.sleep(1)
                                
                        except Exception as notify_err:
                            print(f"⚠️ [Warning] Error in LISTEN loop: {notify_err}")
                            import traceback
                            traceback.print_exc()
                            # Fallback to polling
                            print("   Falling back to polling mode...")
                            break
            
            if mode == "polling":
                # Polling mode with adaptive interval
                print(f"⏳ [System] Polling for new invoices...")
                print(f"   📊 Base interval: {poll_interval}s (when no pending invoices)")
                print(f"   ⚡ Active interval: {poll_interval}s (when processing)")
                
                consecutive_empty_polls = 0
                max_empty_polls = 6  # After 6 empty polls, increase interval
                current_interval = poll_interval
                max_interval = poll_interval * 4  # Max 4x base interval
                
                while True:
                    try:
                        # Process queue (returns True if invoices were processed)
                        has_work = process_queue(worker_conn)
                        
                        if has_work:
                            # Reset interval and counter when work is found
                            consecutive_empty_polls = 0
                            current_interval = poll_interval
                            # Process immediately without delay if work was found
                            # (process_queue already handles all pending invoices)
                            time.sleep(0.5)  # Small delay to prevent tight loop
                        else:
                            # No work found, increase interval gradually
                            consecutive_empty_polls += 1
                            
                            if consecutive_empty_polls >= max_empty_polls:
                                # Increase interval exponentially (up to max_interval)
                                current_interval = min(current_interval * 1.5, max_interval)
                                consecutive_empty_polls = 0  # Reset counter
                                print(f"💤 [System] No pending invoices. Increasing poll interval to {current_interval:.1f}s")
                            
                            time.sleep(current_interval)
                            
                    except Exception as poll_err:
                        print(f"⚠️ [Warning] Error in polling loop: {poll_err}")
                        import traceback
                        traceback.print_exc()
                        # On error, wait before retrying
                        time.sleep(poll_interval)
                
        except Exception as e:
            print(f"❌ [Error] {e}")
            import traceback
            traceback.print_exc()
            print("🔄 [System] Attempting to reconnect in 5 seconds...")
            time.sleep(5)
        finally:
            if subscription:
                try:
                    subscription.unsubscribe()
                except:
                    pass
            if listen_conn: listen_conn.close()
            if worker_conn: worker_conn.close()


if __name__ == "__main__":
    # Determine mode from environment variables
    # Priority: SUPABASE_REALTIME > USE_POLLING > default (realtime)
    use_realtime = os.getenv("USE_SUPABASE_REALTIME", "true").lower() == "true"
    use_polling = os.getenv("USE_POLLING", "false").lower() == "true"
    use_listen = os.getenv("USE_LISTEN_NOTIFY", "false").lower() == "true"
    
    if use_polling:
        mode = "polling"
    elif use_listen:
        mode = "listen"
    elif use_realtime:
        mode = "realtime"
    else:
        mode = "polling"  # Fallback to polling
    
    poll_interval = int(os.getenv("POLL_INTERVAL", "5"))  # Default 5 seconds
    
    main_worker(mode=mode, poll_interval=poll_interval)