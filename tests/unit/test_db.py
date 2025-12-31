from datetime import datetime

import vertex_benchmark.database_utils as db


def _use_temp_db(monkeypatch, tmp_path):
    db_path = tmp_path / "db.sqlite"
    monkeypatch.setattr(db, "DB_FILE", str(db_path))
    return db_path


def test_create_tables_and_roundtrip(monkeypatch, tmp_path):
    db_path = _use_temp_db(monkeypatch, tmp_path)

    db.create_tables()
    assert db_path.exists()

    batch_id = "batch-unit-1"
    with db.get_db_connection_context() as conn:
        db.begin_batch(batch_id, app_version="test", config_json="{}", conn=conn)
        db.insert_benchmark_result(
            batch_id,
            datetime.now(),
            1,
            "europe-west1",
            120.0,
            90.0,
            4,
            "prompt",
            conn=conn,
        )
        db.end_batch(batch_id, conn=conn)
        conn.commit()

    results = db.get_results_by_batch_id(batch_id)
    assert len(results) == 1
    row = results[0]
    assert row["region"] == "europe-west1"
    assert row["pro_time_ms"] == 120.0
    assert row["flash_time_ms"] == 90.0
    assert row["garden_models"] == 4

    assert db.get_latest_batch_id() == batch_id
    batches = db.get_all_batches()
    assert batches and batches[0]["batch_id"] == batch_id
    assert batches[0]["ended_at"] is not None
    all_results = db.get_all_benchmark_results()
    assert len(all_results) == 1


def test_begin_insert_without_conn(monkeypatch, tmp_path):
    _use_temp_db(monkeypatch, tmp_path)

    db.create_tables()
    batch_id = "batch-unit-2"

    db.begin_batch(batch_id, app_version="test", config_json="{}", conn=None)
    db.insert_benchmark_result(
        batch_id,
        datetime.now(),
        1,
        "europe-west4",
        200.0,
        150.0,
        2,
        "prompt-2",
        conn=None,
    )
    db.end_batch(batch_id, conn=None)

    results = db.get_results_by_batch_id(batch_id)
    assert len(results) == 1
    assert results[0]["region"] == "europe-west4"
