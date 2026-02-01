"""
Supabase Realtime client for listening to database changes.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase_client: Client | None = None

def get_supabase_client() -> Client | None:
    """
    Get or create Supabase client instance.
    Requires SUPABASE_URL and SUPABASE_ANON_KEY in .env
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("⚠️ [Supabase] SUPABASE_URL or SUPABASE_ANON_KEY not set in .env")
        print("   Realtime mode will not be available")
        return None
    
    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        print(f"✅ [Supabase] Client initialized")
        return _supabase_client
    except Exception as e:
        print(f"❌ [Supabase] Failed to create client: {e}")
        return None
