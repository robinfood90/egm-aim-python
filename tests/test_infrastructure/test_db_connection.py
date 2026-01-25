import pytest
from src.db.config import get_db_connection

@pytest.fixture
def db_connection():
    """Fixture to get a database connection."""
    connection = get_db_connection()
    yield connection
    if connection:
        connection.close()
        
def test_db_connection_success(db_connection):
    """Test successful database connection."""
    assert db_connection is not None
    assert not db_connection.closed
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        assert list(result.values())[0] == 1