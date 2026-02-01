"""
Test script to verify LISTEN/NOTIFY is working correctly.
Run this script and then upload an invoice to see if notification is received.
"""
import os
import time
from src.db.config import get_listen_connection, get_db_connection
from dotenv import load_dotenv

load_dotenv()

CHANNEL = "invoice_inserted"

def test_listen_notify():
    """Test LISTEN/NOTIFY functionality"""
    print("🧪 [Test] Starting LISTEN/NOTIFY test...")
    
    listen_conn = None
    try:
        # Get LISTEN connection
        listen_conn = get_listen_connection()
        if not listen_conn:
            print("❌ [Test] Failed to establish LISTEN connection")
            return
        
        print(f"✅ [Test] LISTEN connection established")
        print(f"   Host: {os.getenv('DB_HOST')}")
        print(f"   Port: {os.getenv('DB_LISTEN_PORT', '5432')}")
        
        # Register LISTEN
        listen_conn.execute(f"LISTEN {CHANNEL}")
        print(f"📢 [Test] Listening on channel: '{CHANNEL}'")
        print(f"🆔 [Test] Session PID: {listen_conn.pgconn.backend_pid}")
        print("\n⏳ [Test] Waiting for notifications...")
        print("   (Upload an invoice now to trigger notification)")
        print("   (Press Ctrl+C to stop)\n")
        
        # Wait for notifications
        notification_count = 0
        while True:
            try:
                # Use notifies() with timeout (correct way in psycopg3)
                notifies = list(listen_conn.notifies(timeout=10))
                
                if notifies:
                    notification_count += len(notifies)
                    print(f"\n⚡ [Test] Received {len(notifies)} notification(s)!")
                    for n in notifies:
                        print(f"   🔔 Channel: {n.channel}")
                        print(f"   📦 Payload: {n.payload}")
                        print(f"   🆔 PID: {n.pid}")
                    print(f"\n✅ [Test] Total notifications received: {notification_count}")
                    print("⏳ [Test] Waiting for more notifications...\n")
                else:
                    # Timeout - check connection is still alive
                    listen_conn.execute("SELECT 1")
                    print(".", end="", flush=True)
            except KeyboardInterrupt:
                print(f"\n\n🛑 [Test] Stopped by user")
                print(f"📊 [Test] Total notifications received: {notification_count}")
                break
            except Exception as e:
                print(f"\n❌ [Test] Error: {e}")
                break
                
    except Exception as e:
        print(f"❌ [Test] Failed: {e}")
    finally:
        if listen_conn:
            listen_conn.close()
            print("🔌 [Test] Connection closed")

if __name__ == "__main__":
    test_listen_notify()
