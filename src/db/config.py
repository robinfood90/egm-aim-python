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