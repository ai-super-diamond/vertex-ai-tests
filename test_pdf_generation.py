"""Integration-style PDF generation check using the canonical generate_report pipeline."""

import os
import tempfile
import uuid
from datetime import datetime

from PyPDF2 import PdfReader

import vertex_benchmark.database_utils as db
from vertex_benchmark.generate_report import generate_pdf_report


REGIONS = ["europe-west1", "europe-west4", "europe-north1"]


def _seed_db(db_path: str, batch_id: str, cycles: int = 3):
    db.DB_FILE = db_path
    # Fresh DB
    if os.path.exists(db_path):
        os.remove(db_path)
    db.create_tables()

    with db.get_db_connection_context() as conn:
        db.begin_batch(batch_id, app_version="test", config_json="{}", conn=conn)
        for region in REGIONS:
            for cycle in range(1, cycles + 1):
                db.insert_benchmark_result(
                    batch_id,
                    datetime.now(),
                    cycle,
                    region,
                    pro_time_ms=1000 + 10 * cycle,
                    flash_time_ms=500 + 5 * cycle,
                    garden_models=0,
                    test_prompt=f"prompt-{cycle}",
                    conn=conn,
                )
        db.end_batch(batch_id, conn=conn)
        conn.commit()


def test_generate_report_smoke():
    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, "benchmark_results.db")
        pdf_path = os.path.join(td, "out.pdf")
        batch_id = str(uuid.uuid4())

        _seed_db(db_path, batch_id, cycles=3)

        out_file = generate_pdf_report(batch_id=batch_id, output_pdf=pdf_path)
        assert out_file == pdf_path
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000

        reader = PdfReader(pdf_path)
        assert len(reader.pages) > 0
        text = "".join(page.extract_text() or "" for page in reader.pages).lower()
        assert "benchmark" in text
        assert "gemini" in text
        # Ensure cycle count mentioned somewhere
        assert "3" in text
