import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

def get_db_connection(autocommit=False):
    """
    Establishes and returns a connection to the PostgreSQL database using
    environment variables for configuration.
    """
    try:
        conn = psycopg.connect(
            conninfo=(
                f"host={os.getenv('DB_HOST')} "
                f"port={os.getenv('DB_PORT')} "
                f"dbname={os.getenv('DB_NAME')} "
                f"user={os.getenv('DB_USER')} "
                f"password={os.getenv('DB_PASSWORD')} "
                f"sslmode=require"
            ),
            autocommit=autocommit,
            # Vital for Port 6543: Disables prepared statements
            prepare_threshold=None, 
            # Automatically returns results as Python Dictionaries
            row_factory=dict_row 
        )
        return conn
    except Exception as e:
        print(f"❌ Database Connection Error: {e}")
        return None

def get_listen_connection():
    """
    Establishes a connection for LISTEN/NOTIFY.
    For Supabase, we can use the pooler connection (port 6543) 
    as it supports LISTEN/NOTIFY for persistent connections.
    If direct connection is needed, set DB_LISTEN_HOST and DB_LISTEN_PORT in .env
    """
    try:
        # Try direct connection if configured
        listen_host = os.getenv('DB_LISTEN_HOST')
        listen_port = os.getenv('DB_LISTEN_PORT')
        
        if listen_host and listen_port:
            conn = psycopg.connect(
                conninfo=(
                    f"host={listen_host} "
                    f"port={listen_port} "
                    f"dbname={os.getenv('DB_NAME')} "
                    f"user={os.getenv('DB_USER')} "
                    f"password={os.getenv('DB_PASSWORD')} "
                    f"sslmode=require"
                ),
                autocommit=True,  # LISTEN requires autocommit
                row_factory=dict_row 
            )
            return conn
        else:
            # Use pooler connection (works for LISTEN/NOTIFY in Supabase)
            return get_db_connection(autocommit=True)
    except Exception as e:
        print(f"❌ LISTEN Connection Error: {e}")
        print(f"   Trying fallback with pooler connection...")
        # Fallback to pooler connection if direct connection fails
        return get_db_connection(autocommit=True)