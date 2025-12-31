import os
import tempfile
import sqlite3
import gc
from datetime import datetime
from unittest.mock import patch, MagicMock

import vertex_benchmark.database_utils as db
from vertex_benchmark.generate_report import generate_pdf_report


def test_generate_report_no_data_returns_none(db_connection):
    # No data
    with patch('vertex_benchmark.database_utils.get_db_connection') as mock_get_conn:
        mock_get_conn.return_value = db_connection
        out = generate_pdf_report(batch_id="nonexistent", output_pdf=os.path.join(tempfile.gettempdir(), "out.pdf"))
        assert out is None
        assert not os.path.exists(os.path.join(tempfile.gettempdir(), "out.pdf"))


def test_generate_report_partial_and_single_cycle(db_connection):
    batch_id = "edge-batch-1"
    db.begin_batch(batch_id, app_version="test", config_json="{}", conn=db_connection)
    # Insert single cycle for two regions; one with missing Pro, another with missing Flash
    db.insert_benchmark_result(batch_id, datetime.now(), 1, "europe-west1", None, 500.0, 0, "p1", conn=db_connection)
    db.insert_benchmark_result(batch_id, datetime.now(), 1, "europe-west4", 1200.0, None, 0, "p1", conn=db_connection)
    db_connection.commit()
    db.end_batch(batch_id, conn=db_connection)

    # Mock the database operations in generate_report to avoid additional connections
    with patch('vertex_benchmark.generate_report.get_results_by_batch_id') as mock_get_results, \
                 patch('vertex_benchmark.generate_report.get_db_connection') as mock_get_conn:
            
            # Return the expected data for the PDF generation
            mock_data = [
                {
                    'cycle_num': 1,
                    'region': 'europe-west1',
                    'pro_time_ms': None,
                    'flash_time_ms': 500.0,
                    'garden_models': 0,
                    'test_prompt': 'p1'
                },
                {
                    'cycle_num': 1,
                    'region': 'europe-west4',
                    'pro_time_ms': 1200.0,
                    'flash_time_ms': None,
                    'garden_models': 0,
                    'test_prompt': 'p1'
                }
            ]
            mock_get_results.return_value = mock_data
            
            # Mock the connection for batch metadata
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = ('test', '{}', '2023-01-01 00:00:00', '2023-01-01 00:01:00')
            mock_conn.cursor.return_value = mock_cursor
            
            # Make get_db_connection return a context manager
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_conn
            mock_context_manager.__exit__.return_value = None
            mock_get_conn.return_value = mock_context_manager
            
            td = tempfile.gettempdir()
            out_pdf = os.path.join(td, "partial.pdf")
            out = generate_pdf_report(batch_id=batch_id, output_pdf=out_pdf)
            
            assert out == out_pdf
            assert os.path.exists(out_pdf)

