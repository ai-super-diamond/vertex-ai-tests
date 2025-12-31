import os
import tempfile
from datetime import datetime

import vertex_benchmark.database_utils as db


def test_db_batch_and_inserts(db_connection):
    batch_id = "batch-test-123"
    db.begin_batch(batch_id, app_version="test-1.0", config_json="{}", conn=db_connection)

    # one insert
    db.insert_benchmark_result(
        batch_id,
        datetime.now(),
        1,
        "europe-west1",
        100.0,
        80.0,
        5,
        "prompt",
        conn=db_connection,
    )

    # finalize
    db.end_batch(batch_id, conn=db_connection)

    # validate
    results = db.get_results_by_batch_id(batch_id, conn=db_connection)
    assert len(results) == 1

    # Ensure database connection is properly closed
    cur = db_connection.cursor()
    cur.execute("SELECT started_at, ended_at, app_version FROM batches WHERE batch_id=?", (batch_id,))
    row = cur.fetchone()

    assert row is not None
    assert row[0] is not None and row[1] is not None
    assert row[2] == "test-1.0"

