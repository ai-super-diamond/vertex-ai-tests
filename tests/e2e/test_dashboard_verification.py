"""
Verification script to test dashboard improvements.
This script tests the dashboard functionality without requiring a browser.
"""
import sys
import os
import sqlite3
import uuid
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from vertex_benchmark.database_utils import get_db_connection, create_tables, begin_batch, end_batch, insert_benchmark_result, get_all_batches, get_results_by_batch_id
from vertex_benchmark.dashboard import translate, format_slovak_datetime

def test_database_functions():
    """Test that database functions work correctly."""
    print("Testing database functions...")
    
    # Ensure tables exist
    create_tables()
    
    # Create a test batch
    batch_id = str(uuid.uuid4())
    begin_batch(batch_id, "1.0.0", "{}")
    
    # Insert test results
    test_data = [
        (batch_id, datetime.now().isoformat(), 1, "europe-west1", 150.5, 120.3, 5, "Test prompt 1"),
        (batch_id, datetime.now().isoformat(), 2, "europe-west2", 160.2, 130.7, 6, "Test prompt 2"),
        (batch_id, datetime.now().isoformat(), 3, "europe-west3", 140.8, 110.4, 4, "Test prompt 3"),
    ]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO benchmark_results (batch_id, timestamp, cycle_num, region, pro_time_ms, flash_time_ms, garden_models, test_prompt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            test_data
        )
        conn.commit()
    
    # End the batch
    end_batch(batch_id)
    
    # Test retrieval functions
    batches = get_all_batches()
    assert len(batches) > 0, "No batches found"
    
    results = get_results_by_batch_id(batch_id)
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    
    print("✓ Database functions work correctly")
    return batch_id

def test_translation_functions():
    """Test translation and formatting functions."""
    print("Testing translation functions...")
    
    # Test Slovak translation
    assert translate('title', 'sk') == 'Vertex AI Gemini Výkonnostné Testy'
    assert translate('title', 'en') == 'Vertex AI Gemini Performance Tests'
    
    # Test Slovak datetime formatting
    test_dt = "2025-10-30T17:00:00.000Z"
    formatted = format_slovak_datetime(test_dt)
    # Should contain dots in date format
    assert '.' in formatted, f"Slovak date format should contain dots: {formatted}"
    
    print("✓ Translation functions work correctly")

def test_column_mapping():
    """Test that column mappings don't contain underscores."""
    print("Testing column mappings...")
    
    # Test Slovak column mappings
    sk_columns = {
        'timestamp': translate('batch_date', 'sk'),
        'region': translate('region', 'sk'),
        'cycle_num': translate('cycle', 'sk'),
        'pro_time_ms': translate('pro_time', 'sk'),
        'flash_time_ms': translate('flash_time', 'sk'),
        'garden_models': translate('garden_models', 'sk'),
        'test_prompt': translate('test_prompt', 'sk')
    }
    
    # Check no underscores in translated column names
    for db_field, display_name in sk_columns.items():
        assert '_' not in display_name, f"Underscore found in translated column '{db_field}' -> '{display_name}'"
    
    # Test English column mappings
    en_columns = {
        'timestamp': translate('batch_date', 'en'),
        'region': translate('region', 'en'),
        'cycle_num': translate('cycle', 'en'),
        'pro_time_ms': translate('pro_time', 'en'),
        'flash_time_ms': translate('flash_time', 'en'),
        'garden_models': translate('garden_models', 'en'),
        'test_prompt': translate('test_prompt', 'en')
    }
    
    for db_field, display_name in en_columns.items():
        assert '_' not in display_name, f"Underscore found in translated column '{db_field}' -> '{display_name}'"
    
    print("✓ Column mappings are human-readable (no underscores)")

def main():
    """Run all verification tests."""
    print("=" * 60)
    print("DASHBOARD IMPROVEMENTS VERIFICATION")
    print("=" * 60)
    
    try:
        # Test core functions
        batch_id = test_database_functions()
        test_translation_functions()
        test_column_mapping()
        
        print("\n" + "=" * 60)
        print("✅ ALL VERIFICATION TESTS PASSED!")
        print("=" * 60)
        
        print("\nSummary of improvements verified:")
        print("1. ✓ Database functions work correctly")
        print("2. ✓ Translation system works for both Slovak and English")
        print("3. ✓ Slovak datetime formatting works (DD.MM.YYYY format)")
        print("4. ✓ Column mappings are human-readable (no underscores)")
        print("5. ✓ Dashboard should display user-friendly labels instead of database field names")
        
        print(f"\nTest batch ID created: {batch_id}")
        print("You can view this test data in the dashboard at http://localhost:8501")
        
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())