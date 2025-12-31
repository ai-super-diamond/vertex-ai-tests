import pytest
import sqlite3

def init_database(conn):
    """Initialize the database schema on the provided connection."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            cycle_num INTEGER NOT NULL,
            region TEXT NOT NULL,
            pro_time_ms REAL,
            flash_time_ms REAL,
            garden_models INTEGER,
            test_prompt TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            batch_id TEXT PRIMARY KEY,
            started_at DATETIME NOT NULL,
            ended_at DATETIME,
            app_version TEXT,
            config_json TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_results_batch_region
        ON benchmark_results(batch_id, region)
    """)
    conn.commit()

@pytest.fixture
def db_connection():
    """Pytest fixture that provides an in-memory SQLite database connection."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_database(conn)
    yield conn
    conn.close()