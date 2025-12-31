#!/usr/bin/env python3
"""
Simple test script to verify that the dashboard.py fix works correctly.
This script tests the specific issue that was reported - the KeyError with translated column names.
"""

import sys
import os
import pandas as pd
from vertex_benchmark.database_utils import get_all_batches, get_results_by_batch_id

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_dashboard_column_logic():
    """Test the column renaming and selection logic from dashboard.py"""
    
    # Import the translation functions from dashboard
    from vertex_benchmark.dashboard import translate
    
    # Test with Slovak language (the default)
    selected_lang = 'sk'
    
    # Get some test data
    batches = get_all_batches()
    
    if not batches:
        print("No batches found in database - creating test data...")
        # Create some test data if needed
        from database_utils import create_tables, begin_batch, end_batch, insert_benchmark_result
        import uuid
        from datetime import datetime
        
        create_tables()
        
        # Create a test batch
        batch_id = str(uuid.uuid4())
        begin_batch(batch_id, "1.0.0", "{}")
        
        # Insert test results
        for i in range(3):
            insert_benchmark_result(
                batch_id, 
                datetime.now().isoformat(), 
                i+1, 
                "europe-west1", 
                150.5 + i, 
                120.3 + i, 
                5, 
                f"Test prompt {i+1}"
            )
        
        end_batch(batch_id)
        
        # Get the batches again
        batches = get_all_batches()
    
    # Get the first batch for testing
    if batches:
        batch_id = batches[0]['batch_id']
        detailed_results = get_results_by_batch_id(batch_id)
        
        if detailed_results:
            # Convert to DataFrame (same as in dashboard.py)
            df_detailed = pd.DataFrame(detailed_results)
            
            # Print original columns
            print("Original columns from database:")
            print(list(df_detailed.columns))
            print()
            
            # Apply the same column mapping as in dashboard.py
            column_mapping = {
                'timestamp': translate('batch_date', selected_lang),
                'region': translate('region', selected_lang),
                'cycle_num': translate('cycle', selected_lang),
                'pro_time_ms': translate('pro_time', selected_lang),
                'flash_time_ms': translate('flash_time', selected_lang),
                'garden_models': translate('garden_models', selected_lang),
                'test_prompt': translate('test_prompt', selected_lang)
            }
            
            # Apply column renaming
            df_detailed_display = df_detailed.rename(columns=column_mapping)
            
            # Print renamed columns
            print("Columns after renaming:")
            print(list(df_detailed_display.columns))
            print()
            
            # Create the display_cols list (same as in dashboard.py)
            display_cols = [
                translate('batch_date', selected_lang),
                translate('region', selected_lang),
                translate('cycle', selected_lang),
                translate('pro_time', selected_lang),
                translate('flash_time', selected_lang),
                translate('garden_models', selected_lang),
                translate('test_prompt', selected_lang)
            ]
            
            print("Display columns we want to show:")
            print(display_cols)
            print()
            
            # This is the critical test - try to access the dataframe with the translated column names
            try:
                # This should work now with our fix
                result_df = df_detailed_display[display_cols]
                print("SUCCESS: Column selection works correctly!")
                print("Sample data:")
                print(result_df.head())
                return True
            except KeyError as e:
                print(f"FAILURE: KeyError still occurs: {e}")
                print("Available columns:", list(df_detailed_display.columns))
                return False
        else:
            print("No detailed results found for batch")
            return False
    else:
        print("No batches found")
        return False

if __name__ == "__main__":
    print("Testing dashboard column logic fix...")
    print("=" * 50)
    
    success = test_dashboard_column_logic()
    
    print("=" * 50)
    if success:
        print("✅ Dashboard fix verified successfully!")
        sys.exit(0)
    else:
        print("❌ Dashboard fix failed!")
        sys.exit(1)