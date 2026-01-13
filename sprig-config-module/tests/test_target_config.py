"""Quick smoke test for _target_ config loading."""

from tests.db.mssql.mssql_database_adapter import MSSQLDatabase

def test_target_config():
    """Test that MSSQLDatabase can be instantiated."""
    db = MSSQLDatabase(url="mssql://localhost", port=1234, database="test")

    assert db.url == "mssql://localhost"
    assert db.port == 1234
    assert db.database == "test"
