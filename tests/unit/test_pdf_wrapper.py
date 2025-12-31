import os
import tempfile
import sqlite3
import gc
from datetime import datetime
import uuid
from unittest.mock import patch, MagicMock

import vertex_benchmark.database_utils as db
from vertex_benchmark.generate_report import generate_pdf_report


def test_generate_report_happy_path(db_connection):
    batch_id = str(uuid.uuid4())
    db.begin_batch(batch_id, app_version="test", config_json="{}", conn=db_connection)
    # create small dataset: 1 region x 2 cycles
    for cycle in (1, 2):
        db.insert_benchmark_result(
            batch_id,
            datetime.now(),
            cycle,
            "europe-west1",
            1000.0 + cycle,
            800.0 + cycle,
            0,
            f"p{cycle}",
            conn=db_connection,
        )
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
                    'pro_time_ms': 1001.0,
                    'flash_time_ms': 801.0,
                    'garden_models': 0,
                    'test_prompt': 'p1'
                },
                {
                    'cycle_num': 2,
                    'region': 'europe-west1',
                    'pro_time_ms': 1002.0,
                    'flash_time_ms': 802.0,
                    'garden_models': 0,
                    'test_prompt': 'p2'
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
            out_pdf = os.path.join(td, "wrap.pdf")
            out = generate_pdf_report(batch_id=batch_id, output_pdf=out_pdf)
            
            assert out == out_pdf
            assert os.path.exists(out_pdf)

