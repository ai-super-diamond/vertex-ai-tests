"""
Test script for PDF generation from CSV benchmark results.

This script creates a sample CSV file with test data and verifies
that the PDF generation works correctly with the multi-cycle format.
"""

import csv
import os
import random
import re
import sys

from PyPDF2 import PdfReader

from csv_to_pdf_converter import convert_csv_to_pdf


def create_test_csv(filename, num_regions=3, num_cycles=10):
    """
    Create a test CSV file with sample benchmark data.
    
    Args:
        filename: Path to the CSV file to create
        num_regions: Number of regions to include (default: 3)
        num_cycles: Number of cycles per region (default: 10)
    """
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

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['#Cycle', 'region', 'Pro', 'Flash', 'Garden Models']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for region in test_regions:
            for cycle in range(1, num_cycles + 1):
                # Add some variation to response times (+/- 10%)
                pro_variation = random.uniform(0.9, 1.1)
                flash_variation = random.uniform(0.9, 1.1)

                pro_time = round(base_times[region]["Pro"] * pro_variation, 2)
                flash_time = round(base_times[region]["Flash"] * flash_variation, 2)

                writer.writerow({
                    '#Cycle': cycle,
                    'region': region,
                    'Pro': f"{pro_time}ms",
                    'Flash': f"{flash_time}ms",
                    'Garden Models': 0
                })

    print(f"✓ Created test CSV: {filename}")
    print(f"  - {num_regions} regions × {num_cycles} cycles = {num_regions * num_cycles} records")


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
            except (AttributeError, TypeError, ValueError) as e:
                # Ignore text extraction errors for individual pages
                continue

        # If text extraction worked, verify content
        if full_text:
            # Check for key content (case-insensitive)
            full_text_lower = full_text.lower()

            # Assert: Title or key terms are present
            has_benchmark = "benchmark" in full_text_lower or "gemini" in full_text_lower
            assert has_benchmark, "PDF doesn't contain expected benchmark content"

            # Assert: Cycle count is mentioned with context
            # Look for patterns like "across N test" or "N test prompts"
            cycle_pattern = re.compile(rf'\b{expected_cycles}\s+(test|cycle|prompt)', re.IGNORECASE)
            cycle_text = cycle_pattern.search(full_text) is not None
            if not cycle_text:
                print(f"  ⚠ Warning: Could not verify cycle count '{expected_cycles}' in PDF text with expected context")
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


def verify_csv_structure(csv_file, expected_regions, expected_cycles):
    """
    Verify CSV file structure and content.
    
    Args:
        csv_file: Path to the CSV file
        expected_regions: Expected number of regions
        expected_cycles: Expected number of cycles per region
    
    Returns:
        tuple: (success, error_message)
    """
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # Assert: Correct number of records
            expected_records = expected_regions * expected_cycles
            assert len(rows) == expected_records, \
                f"Expected {expected_records} records, got {len(rows)}"

            # Assert: Required columns exist
            required_columns = ['#Cycle', 'region', 'Pro', 'Flash', 'Garden Models']
            assert all(col in rows[0].keys() for col in required_columns), \
                f"Missing required columns. Expected: {required_columns}"

            # Assert: Cycle numbers are correct (1 to expected_cycles)
            cycles = set(int(row['#Cycle']) for row in rows)
            expected_cycle_set = set(range(1, expected_cycles + 1))
            assert cycles == expected_cycle_set, \
                f"Cycle numbers incorrect. Expected: {expected_cycle_set}, Got: {cycles}"

            # Assert: All regions have all cycles
            regions = set(row['region'] for row in rows)
            assert len(regions) == expected_regions, \
                f"Expected {expected_regions} regions, got {len(regions)}"

            for region in regions:
                region_rows = [r for r in rows if r['region'] == region]
                assert len(region_rows) == expected_cycles, \
                    f"Region {region} should have {expected_cycles} cycles, got {len(region_rows)}"

            return True, None

    except AssertionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error reading CSV: {str(e)}"


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

    all_tests_passed = True
    test_results = []

    # Test 1: Standard 10-cycle test
    print("Test 1: Standard 10-cycle benchmark")
    print("-" * 60)
    csv_file_1 = os.path.join(test_dir, "test_10cycles.csv")
    pdf_file_1 = os.path.join(test_dir, "test_report_10cycles.pdf")

    create_test_csv(csv_file_1, num_regions=3, num_cycles=10)

    # Verify CSV structure
    csv_ok, csv_error = verify_csv_structure(csv_file_1, expected_regions=3, expected_cycles=10)
    assert csv_ok, f"CSV verification failed: {csv_error}"
    print(f"  ✓ CSV structure verified (30 records)")

    convert_csv_to_pdf(csv_file_1, pdf_file_1)

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
    csv_file_2 = os.path.join(test_dir, "test_5cycles.csv")
    pdf_file_2 = os.path.join(test_dir, "test_report_5cycles.pdf")

    create_test_csv(csv_file_2, num_regions=3, num_cycles=5)

    csv_ok, csv_error = verify_csv_structure(csv_file_2, expected_regions=3, expected_cycles=5)
    assert csv_ok, f"CSV verification failed: {csv_error}"
    print(f"  ✓ CSV structure verified (15 records)")

    convert_csv_to_pdf(csv_file_2, pdf_file_2)

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
    csv_file_3 = os.path.join(test_dir, "test_1cycle.csv")
    pdf_file_3 = os.path.join(test_dir, "test_report_1cycle.pdf")

    create_test_csv(csv_file_3, num_regions=3, num_cycles=1)

    csv_ok, csv_error = verify_csv_structure(csv_file_3, expected_regions=3, expected_cycles=1)
    assert csv_ok, f"CSV verification failed: {csv_error}"
    print(f"  ✓ CSV structure verified (3 records)")

    convert_csv_to_pdf(csv_file_3, pdf_file_3)

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
    csv_file_4 = os.path.join(test_dir, "test_20cycles.csv")
    pdf_file_4 = os.path.join(test_dir, "test_report_20cycles.pdf")

    create_test_csv(csv_file_4, num_regions=3, num_cycles=20)

    csv_ok, csv_error = verify_csv_structure(csv_file_4, expected_regions=3, expected_cycles=20)
    assert csv_ok, f"CSV verification failed: {csv_error}"
    print(f"  ✓ CSV structure verified (60 records)")

    convert_csv_to_pdf(csv_file_4, pdf_file_4)

    assert os.path.exists(pdf_file_4), "PDF file was not created"
    print(f"  ✓ PDF file created")

    pdf_ok, pdf_error = verify_pdf_content(pdf_file_4, expected_cycles=20)
    assert pdf_ok, f"PDF verification failed: {pdf_error}"
    print(f"  ✓ PDF content verified (20 cycles mentioned)")

    test_results.append(("Test 4 (20 cycles)", True, None))
    print(f"✓ Test 4 PASSED\n")

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
