"""Deprecated shim: CSV-to-PDF path removed in favor of generate_report over SQLite.

Use vertex_benchmark.generate_report.generate_pdf_report with database inputs instead.
This file remains to avoid import errors but intentionally raises to steer callers to
the canonical implementation.
"""

def convert_csv_to_pdf(*_, **__):
    raise RuntimeError(
        "csv_to_pdf_converter is deprecated. Seed the database and call generate_pdf_report instead."
    )
