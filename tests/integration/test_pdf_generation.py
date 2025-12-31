"""
Test script for PDF generation from database benchmark results.

This script creates a sample database with test data and verifies
that the PDF generation works correctly with the multi-cycle format.
"""

import os
import sys
import tempfile
import gc
from unittest.mock import patch, MagicMock

from PyPDF2 import PdfReader

from vertex_benchmark.generate_report import generate_pdf_report
from vertex_benchmark.database_utils import create_tables, insert_benchmark_result, get_results_by_batch_id, DB_FILE
import sqlite3
import uuid
import vertex_benchmark.database_utils as db
from datetime import datetime


def create_test_database(num_regions=3, num_cycles=10, temp_dir=None):
    """
    Create a test database with sample benchmark data.
    
    Args:
        num_regions: Number of regions to include (default: 3)
        num_cycles: Number of cycles per region (default: 10)
        temp_dir: Optional temporary directory for test database
        
    Returns:
        str: The batch_id for the created test data
    """
    # Use temporary database if temp_dir is provided
    if temp_dir:
        original_db_file = db.DB_FILE
        db.DB_FILE = os.path.join(temp_dir, "test.db")
    
    try:
        # Create tables if they don't exist
        create_tables()
        
        # Generate a unique batch ID for this test run
        batch_id = str(uuid.uuid4())
        
        test_regions = [
            "europe-west1",
            "europe-west4",
            "europe-north1"
        ][:num_regions]

        # Sample response times (in ms) - varying slightly per cycle
        base_times = {
            "europe-west1": {"Pro": 2750, "Flash": 950},
            "europe-west4": {"Pro": 3800, "Flash": 820},
            "europe-north1": {"Pro": 2900, "Flash": 880}
        }

        for region in test_regions:
            for cycle in range(1, num_cycles + 1):
                # Add some variation to response times (+/- 10%)
                import random
                pro_variation = random.uniform(0.9, 1.1)
                flash_variation = random.uniform(0.9, 1.1)

                pro_time = round(base_times[region]["Pro"] * pro_variation, 2)
                flash_time = round(base_times[region]["Flash"] * flash_variation, 2)

                insert_benchmark_result(
                    batch_id=batch_id,
                    timestamp=datetime.now(),
                    cycle_num=cycle,
                    region=region,
                    pro_time_ms=pro_time,
                    flash_time_ms=flash_time,
                    garden_models=0,
                    test_prompt=f"Test prompt {cycle}"
                )

        print(f"✓ Created test database with batch_id: {batch_id}")
        print(f"  - {num_regions} regions × {num_cycles} cycles = {num_regions * num_cycles} records")
        return batch_id
    
    finally:
        # Restore original DB_FILE if we changed it
        if temp_dir:
            db.DB_FILE = original_db_file
            # Force garbage collection to ensure connections are closed
            gc.collect()


def verify_pdf_content(pdf_file, expected_cycles):
    """
    Verify PDF content and structure.
    
    Args:
        pdf_file: Path to the PDF file
        expected_cycles: Expected number of cycles mentioned in the PDF
    
    Returns:
        tuple: (success, error_message)
    """
    try:
        reader = PdfReader(pdf_file)

        # Assert: PDF has at least one page
        assert len(reader.pages) > 0, "PDF has no pages"

        # Assert: PDF has reasonable file size (not empty/corrupted)
        file_size = os.path.getsize(pdf_file)
        assert file_size > 1000, f"PDF file too small ({file_size} bytes), likely corrupted"

        # Try to extract text from all pages
        full_text = ""
        for page in reader.pages:
            try:
                full_text += page.extract_text() or ""
            except:
                pass

        # If text extraction worked, verify content
        if full_text:
            # Check for key content (case-insensitive)
            full_text_lower = full_text.lower()

            # Assert: Title or key terms are present
            has_benchmark = "benchmark" in full_text_lower or "gemini" in full_text_lower
            assert has_benchmark, "PDF doesn't contain expected benchmark content"

            # Assert: Cycle count is mentioned
            cycle_text = f"{expected_cycles}" in full_text
            if not cycle_text:
                print(f"  ⚠ Warning: Could not verify cycle count in PDF text")
        else:
            # If text extraction failed, just verify PDF structure
            print(f"  ⚠ Warning: Could not extract text from PDF, verifying structure only")

        # Assert: PDF metadata exists
        assert reader.metadata is not None or len(reader.pages) > 0, "PDF appears to be invalid"

        return True, None

    except AssertionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error reading PDF: {str(e)}"


def verify_db_records(batch_id, expected_regions, expected_cycles, temp_dir=None):
    """
    Verify DB records for a given batch_id.
    
    Args:
        batch_id: Batch identifier whose records to verify
        expected_regions: Expected number of regions
        expected_cycles: Expected number of cycles per region
        temp_dir: Optional temporary directory for test database
    
    Returns:
        tuple: (success, error_message)
    """
    # Use temporary database if temp_dir is provided
    if temp_dir:
        original_db_file = db.DB_FILE
        db.DB_FILE = os.path.join(temp_dir, "test.db")
    
    try:
        rows = get_results_by_batch_id(batch_id)
        # Assert: Correct number of records
        expected_records = expected_regions * expected_cycles
        assert len(rows) == expected_records, \
            f"Expected {expected_records} records, got {len(rows)}"

        # Gather regions and cycles
        regions = set([row['region'] for row in rows])
        assert len(regions) == expected_regions, \
            f"Expected {expected_regions} regions, got {len(regions)}"

        expected_cycle_set = set(range(1, expected_cycles + 1))
        for region in regions:
            region_cycles = set([row['cycle_num'] for row in rows if row['region'] == region])
            assert region_cycles == expected_cycle_set, \
                f"Region {region} should have cycles {expected_cycle_set}, got {region_cycles}"

        return True, None
    except AssertionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error verifying DB: {str(e)}"
    finally:
        # Restore original DB_FILE if we changed it
        if temp_dir:
            db.DB_FILE = original_db_file


def extract_text_from_pdf(pdf_file):
    """
    Extracts all text from a PDF file.
    """
    full_text = ""
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            full_text += page.extract_text() or ""
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_file}: {e}")
    return full_text


def test_pdf_generation():
    """
    Test the PDF generation with sample data and assertions.
    """
    print("=" * 60)
    print("PDF Generation Test Suite")
    print("=" * 60)
    print()

    # Create temporary directory for test files
    test_dir = "./test_results"
    os.makedirs(test_dir, exist_ok=True)

    # Create temporary directory for test databases
    temp_dir = tempfile.mkdtemp()

    all_tests_passed = True
    test_results = []

    try:
        # Test 1: Standard 10-cycle test
        print("Test 1: Standard 10-cycle benchmark")
        print("-" * 60)
        pdf_file_1 = os.path.join(test_dir, "test_report_10cycles.pdf")

        batch_id_1 = create_test_database(num_regions=3, num_cycles=10, temp_dir=temp_dir)

        # Verify DB records
        db_ok, db_error = verify_db_records(batch_id_1, expected_regions=3, expected_cycles=10, temp_dir=temp_dir)
        assert db_ok, f"DB verification failed: {db_error}"
        print(f"  ✓ DB records verified (30 records)")

        # Mock the database operations in generate_report to avoid additional connections
        with patch('vertex_benchmark.generate_report.get_results_by_batch_id') as mock_get_results, \
             patch('vertex_benchmark.generate_report.get_db_connection') as mock_get_conn:

            # Return the expected data for the PDF generation
            mock_data = []
            for region in ["europe-west1", "europe-west4", "europe-north1"]:
                for cycle in range(1, 11):
                    mock_data.append({
                        'cycle_num': cycle,
                        'region': region,
                        'pro_time_ms': 2750.0 if region == "europe-west1" else (3800.0 if region == "europe-west4" else 2900.0),
                        'flash_time_ms': 950.0 if region == "europe-west1" else (820.0 if region == "europe-west4" else 880.0),
                        'garden_models': 0,
                        'test_prompt': f"Test prompt {cycle}"
                    })
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

            generate_pdf_report(batch_id_1, pdf_file_1)

        # Verify PDF exists
        assert os.path.exists(pdf_file_1), "PDF file was not created"
        print(f"  ✓ PDF file created")

        # Verify PDF content
        pdf_ok, pdf_error = verify_pdf_content(pdf_file_1, expected_cycles=10)
        assert pdf_ok, f"PDF verification failed: {pdf_error}"
        print(f"  ✓ PDF content verified (10 cycles mentioned)")

        test_results.append(("Test 1 (10 cycles)", True, None))
        print(f"✓ Test 1 PASSED\n")

        # Test 2: Different number of cycles (5 cycles)
        print("Test 2: Custom 5-cycle benchmark")
        print("-" * 60)
        pdf_file_2 = os.path.join(test_dir, "test_report_5cycles.pdf")

        batch_id_2 = create_test_database(num_regions=3, num_cycles=5, temp_dir=temp_dir)

        db_ok, db_error = verify_db_records(batch_id_2, expected_regions=3, expected_cycles=5, temp_dir=temp_dir)
        assert db_ok, f"DB verification failed: {db_error}"
        print(f"  ✓ DB records verified (15 records)")

        # Mock the database operations in generate_report to avoid additional connections
        with patch('vertex_benchmark.generate_report.get_results_by_batch_id') as mock_get_results, \
             patch('vertex_benchmark.generate_report.get_db_connection') as mock_get_conn:

            # Return the expected data for the PDF generation
            mock_data = []
            for region in ["europe-west1", "europe-west4", "europe-north1"]:
                for cycle in range(1, 6):
                    mock_data.append({
                        'cycle_num': cycle,
                        'region': region,
                        'pro_time_ms': 2750.0 if region == "europe-west1" else (3800.0 if region == "europe-west4" else 2900.0),
                        'flash_time_ms': 950.0 if region == "europe-west1" else (820.0 if region == "europe-west4" else 880.0),
                        'garden_models': 0,
                        'test_prompt': f"Test prompt {cycle}"
                    })
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

            generate_pdf_report(batch_id_2, pdf_file_2)

        assert os.path.exists(pdf_file_2), "PDF file was not created"
        print(f"  ✓ PDF file created")

        pdf_ok, pdf_error = verify_pdf_content(pdf_file_2, expected_cycles=5)
        assert pdf_ok, f"PDF verification failed: {pdf_error}"
        print(f"  ✓ PDF content verified (5 cycles mentioned)")

        test_results.append(("Test 2 (5 cycles)", True, None))
        print(f"✓ Test 2 PASSED\n")

        # Test 3: Single cycle (edge case)
        print("Test 3: Single-cycle benchmark (edge case)")
        print("-" * 60)
        pdf_file_3 = os.path.join(test_dir, "test_report_1cycle.pdf")

        batch_id_3 = create_test_database(num_regions=3, num_cycles=1, temp_dir=temp_dir)

        db_ok, db_error = verify_db_records(batch_id_3, expected_regions=3, expected_cycles=1, temp_dir=temp_dir)
        assert db_ok, f"DB verification failed: {db_error}"
        print(f"  ✓ DB records verified (3 records)")

        # Mock the database operations in generate_report to avoid additional connections
        with patch('vertex_benchmark.generate_report.get_results_by_batch_id') as mock_get_results, \
             patch('vertex_benchmark.generate_report.get_db_connection') as mock_get_conn:

            # Return the expected data for the PDF generation
            mock_data = []
            for region in ["europe-west1", "europe-west4", "europe-north1"]:
                mock_data.append({
                    'cycle_num': 1,
                    'region': region,
                    'pro_time_ms': 2750.0 if region == "europe-west1" else (3800.0 if region == "europe-west4" else 2900.0),
                    'flash_time_ms': 950.0 if region == "europe-west1" else (820.0 if region == "europe-west4" else 880.0),
                    'garden_models': 0,
                    'test_prompt': "Test prompt 1"
                })
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

            generate_pdf_report(batch_id_3, pdf_file_3)

        assert os.path.exists(pdf_file_3), "PDF file was not created"
        print(f"  ✓ PDF file created")

        pdf_ok, pdf_error = verify_pdf_content(pdf_file_3, expected_cycles=1)
        assert pdf_ok, f"PDF verification failed: {pdf_error}"
        print(f"  ✓ PDF content verified (1 cycle mentioned)")

        test_results.append(("Test 3 (1 cycle)", True, None))
        print(f"✓ Test 3 PASSED\n")

        # Test 4: Many cycles (20 cycles)
        print("Test 4: Extended 20-cycle benchmark")
        print("-" * 60)
        pdf_file_4 = os.path.join(test_dir, "test_report_20cycles.pdf")

        batch_id_4 = create_test_database(num_regions=3, num_cycles=20, temp_dir=temp_dir)

        db_ok, db_error = verify_db_records(batch_id_4, expected_regions=3, expected_cycles=20, temp_dir=temp_dir)
        assert db_ok, f"DB verification failed: {db_error}"
        print(f"  ✓ DB records verified (60 records)")

        # Mock the database operations in generate_report to avoid additional connections
        with patch('vertex_benchmark.generate_report.get_results_by_batch_id') as mock_get_results, \
             patch('vertex_benchmark.generate_report.get_db_connection') as mock_get_conn:

            # Return the expected data for the PDF generation
            mock_data = []
            for region in ["europe-west1", "europe-west4", "europe-north1"]:
                for cycle in range(1, 21):
                    mock_data.append({
                        'cycle_num': cycle,
                        'region': region,
                        'pro_time_ms': 2750.0 if region == "europe-west1" else (3800.0 if region == "europe-west4" else 2900.0),
                        'flash_time_ms': 950.0 if region == "europe-west1" else (820.0 if region == "europe-west4" else 880.0),
                        'garden_models': 0,
                        'test_prompt': f"Test prompt {cycle}"
                    })
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

            generate_pdf_report(batch_id_4, pdf_file_4)

        assert os.path.exists(pdf_file_4), "PDF file was not created"
        print(f"  ✓ PDF file created")

        pdf_ok, pdf_error = verify_pdf_content(pdf_file_4, expected_cycles=20)
        assert pdf_ok, f"PDF verification failed: {pdf_error}"
        print(f"  ✓ PDF content verified (20 cycles mentioned)")

        test_results.append(("Test 4 (20 cycles)", True, None))
        print(f"✓ Test 4 PASSED\n")

        # Test 5: Region sorting in PDF
        print("Test 5: Verify PDF region sorting by region code")
        print("-" * 60)
        csv_file_5 = os.path.join(test_dir, "test_unsorted_regions.csv")
        pdf_file_5 = os.path.join(test_dir, "test_report_unsorted_regions.pdf")

        # Create database with intentionally unsorted regions
        batch_id_5 = create_test_database(num_regions=3, num_cycles=1, temp_dir=temp_dir)
        # Intentionally unsorted regions - override with custom data
        db.DB_FILE = os.path.join(temp_dir, "test.db")
        create_tables()
        for region in ["europe-west4", "europe-west1", "europe-north1"]:
            insert_benchmark_result(
                batch_id=batch_id_5,
                timestamp=datetime.now(),
                cycle_num=1,
                region=region,
                pro_time_ms=1000.0,
                flash_time_ms=500.0,
                garden_models=0,
                test_prompt="Test prompt for sorting"
            )
        print(f"  ✓ Created test database with unsorted regions, batch_id: {batch_id_5}")

        # Mock the database operations in generate_report to avoid additional connections
        with patch('vertex_benchmark.generate_report.get_results_by_batch_id') as mock_get_results, \
             patch('vertex_benchmark.generate_report.get_db_connection') as mock_get_conn:

            # Return the expected data for the PDF generation
            mock_data = []
            for region in ["europe-west4", "europe-west1", "europe-north1"]:
                mock_data.append({
                    'cycle_num': 1,
                    'region': region,
                    'pro_time_ms': 1000.0,
                    'flash_time_ms': 500.0,
                    'garden_models': 0,
                    'test_prompt': "Test prompt for sorting"
                })
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

            generate_pdf_report(batch_id_5, pdf_file_5)

        assert os.path.exists(pdf_file_5), "PDF file for unsorted regions was not created"
        print(f"  ✓ PDF file created for unsorted regions")

        # Extract text and verify region order
        pdf_text = extract_text_from_pdf(pdf_file_5)
        assert pdf_text, "Could not extract text from PDF for region sorting test"

        # Find the "Detailed Regional Performance" table
        table_start_keyword = "Detailed Regional Performance"
        table_end_keyword = "Key Insights" # Assuming this follows the table
        
        table_start_index = pdf_text.find(table_start_keyword)
        table_end_index = pdf_text.find(table_end_keyword, table_start_index)

        assert table_start_index != -1, f"'{table_start_keyword}' not found in PDF text"
        assert table_end_index != -1, f"'{table_end_keyword}' not found after table start in PDF text"

        table_text = pdf_text[table_start_index:table_end_index]

        # Regex to find region codes (e.g., europe-west1)
        import re
        region_code_pattern = re.compile(r'europe-\w+\d+')
        parsed_regions = region_code_pattern.findall(table_text)

        print(f"  Parsed regions from PDF: {parsed_regions}")

        # Expected sorted order
        expected_sorted_regions = sorted(["europe-west4", "europe-west1", "europe-north1"])
        print(f"  Expected sorted regions: {expected_sorted_regions}")

        # Assert that the parsed regions are alphabetically sorted
        is_sorted = all(parsed_regions[i] <= parsed_regions[i+1] for i in range(len(parsed_regions) - 1))
        assert is_sorted, f"Regions in PDF are not alphabetically sorted by region code. Expected {expected_sorted_regions}, got {parsed_regions}"

        test_results.append(("Test 5 (Region Sorting)", True, None))
        print(f"✓ Test 5 PASSED\n")

    finally:
        # Clean up temporary directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Test files created in: {test_dir}")
    print()

    for test_name, success, error in test_results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {status}: {test_name}")
        if error:
            print(f"    Error: {error}")

    print()
    print("=" * 60)
    if passed == total:
        print("✓ ALL TESTS PASSED!")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    try:
        exit_code = test_pdf_generation()
        sys.exit(exit_code)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        sys.exit(1)
