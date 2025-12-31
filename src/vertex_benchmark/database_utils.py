import sqlite3
import uuid
from datetime import datetime
from contextlib import contextmanager

DB_FILE = "benchmark_results.db"

def get_db_connection():
    """Creates and returns a connection to the SQLite database with sane PRAGMAs."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        # Improve concurrency and throughput for bulk inserts
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA cache_size=10000;")
        conn.execute("PRAGMA temp_store=MEMORY;")
    except Exception:
        # PRAGMAs are best-effort; ignore failures on older SQLite versions
        pass
    return conn

@contextmanager
def get_db_connection_context():
    """Context manager for database connections with sane PRAGMAs."""
    conn = None
    try:
        conn = get_db_connection()
        yield conn
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def create_tables():
    """Creates the necessary database tables if they don't exist.

    If tables already exist, add new columns best-effort (idempotent ALTERs).
    """
    with get_db_connection_context() as conn:
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
                test_prompt TEXT NOT NULL,
                pro_error TEXT,
                flash_error TEXT
            )
        """)
        # Add new columns if table pre-existed without them
        for col in ("pro_error", "flash_error"):
            try:
                cursor.execute(f"ALTER TABLE benchmark_results ADD COLUMN {col} TEXT")
            except Exception:
                # Ignore if column already exists or ALTER not needed
                pass

        # Batches metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                batch_id TEXT PRIMARY KEY,
                started_at DATETIME NOT NULL,
                ended_at DATETIME,
                app_version TEXT,
                config_json TEXT NOT NULL
            )
        """)
        # Composite index for faster report queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_results_batch_region
            ON benchmark_results(batch_id, region)
        """)
        conn.commit()

def insert_benchmark_result(batch_id, timestamp, cycle_num, region, pro_time_ms, flash_time_ms, garden_models, test_prompt, pro_error=None, flash_error=None, conn=None):
    """Inserts a single benchmark result into the database.

    If `conn` is provided, reuse it without committing; caller manages transaction.
    Otherwise, open a new connection for this insert and commit immediately.
    """
    params = (batch_id, timestamp, cycle_num, region, pro_time_ms, flash_time_ms, garden_models, test_prompt, pro_error, flash_error)
    if conn is not None:
        # Use the provided connection without committing
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO benchmark_results (batch_id, timestamp, cycle_num, region, pro_time_ms, flash_time_ms, garden_models, test_prompt, pro_error, flash_error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, params)
    else:
        # Open a new connection and commit immediately
        with get_db_connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO benchmark_results (batch_id, timestamp, cycle_num, region, pro_time_ms, flash_time_ms, garden_models, test_prompt, pro_error, flash_error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, params)
            conn.commit()

def get_latest_batch_id():
    """Retrieves the latest batch_id from the database."""
    with get_db_connection_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT batch_id FROM benchmark_results ORDER BY timestamp DESC LIMIT 1")
        result = cursor.fetchone()
        return result['batch_id'] if result else None

def get_results_by_batch_id(batch_id, conn=None):
    """Fetches all benchmark results for a given batch_id."""
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM benchmark_results WHERE batch_id = ?", (batch_id,))
        results = cursor.fetchall()
        return [dict(row) for row in results]
    else:
        with get_db_connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM benchmark_results WHERE batch_id = ?", (batch_id,))
            results = cursor.fetchall()
            return [dict(row) for row in results]

def get_all_batches():
    """Fetches all batches from the database."""
    with get_db_connection_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM batches ORDER BY started_at DESC")
        results = cursor.fetchall()
        return [dict(row) for row in results]

def get_all_benchmark_results():
    """Fetches all benchmark results from the database."""
    with get_db_connection_context() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM benchmark_results ORDER BY timestamp DESC")
        results = cursor.fetchall()
        return [dict(row) for row in results]

def begin_batch(batch_id: str, app_version: str, config_json: str, conn=None):
    """Insert a batches row to mark batch start."""
    if conn is not None:
        # Use the provided connection without committing
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO batches (batch_id, started_at, ended_at, app_version, config_json)
            VALUES (?, ?, NULL, ?, ?)
            """,
            (batch_id, datetime.now(), app_version, config_json),
        )
    else:
        # Open a new connection and commit immediately
        with get_db_connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO batches (batch_id, started_at, ended_at, app_version, config_json)
                VALUES (?, ?, NULL, ?, ?)
                """,
                (batch_id, datetime.now(), app_version, config_json),
            )
            conn.commit()

def end_batch(batch_id: str, conn=None):
    """Update a batches row to mark batch completion time."""
    if conn is not None:
        # Use the provided connection without committing
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE batches SET ended_at = ? WHERE batch_id = ?
            """,
            (datetime.now(), batch_id),
        )
    else:
        # Open a new connection and commit immediately
        with get_db_connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE batches SET ended_at = ? WHERE batch_id = ?
                """,
                (datetime.now(), batch_id),
            )
            conn.commit()

if __name__ == "__main__":
    create_tables()
    print("Database and table 'benchmark_results' ensured to exist.")
    # Example usage:
    # new_batch_id = str(uuid.uuid4())
    # insert_benchmark_result(new_batch_id, datetime.now(), 1, "europe-west1", 123.45, 67.89, 5, "Test prompt 1")
    # insert_benchmark_result(new_batch_id, datetime.now(), 2, "europe-west1", 130.00, 70.00, 5, "Test prompt 2")
    # latest_id = get_latest_batch_id()
    # print(f"Latest batch ID: {latest_id}")
    # if latest_id:
    #     batch_results = get_results_by_batch_id(latest_id)
    #     for row in batch_results:
    #         print(dict(row))