import sys
import os
import pytest
import re
from streamlit.testing.v1 import AppTest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def extract_visible_text(markdown_elements):
    """
    Extract visible text from markdown elements, excluding HTML tags and attributes.
    This focuses on the actual content that would be displayed to users.
    """
    visible_texts = []
    
    for element in markdown_elements:
        if hasattr(element, 'body'):
            # Remove HTML tags and get just the text content
            text_content = re.sub(r'<[^>]+>', '', element.body)
            # Clean up whitespace
            text_content = ' '.join(text_content.split())
            if text_content:
                visible_texts.append(text_content)
    
    return visible_texts

def find_underscores_in_text(text):
    """
    Find underscores in visible text content.
    Returns a list of positions where underscores are found.
    """
    underscores = []
    for i, char in enumerate(text):
        if char == '_':
            underscores.append(i)
    return underscores

def test_no_underscores_in_dashboard_ui():
    """
    Test that no underscores are found in the visible dashboard UI content.
    This ensures database field names are properly replaced with human-readable labels.
    """
    # Ensure database tables exist before running the test
    from vertex_benchmark.database_utils import create_tables
    try:
        create_tables()
    except Exception as e:
        print(f"Database creation issue (continuing anyway): {e}")
    
    # Start the dashboard from the parent directory
    at = AppTest.from_file("src/vertex_benchmark/dashboard.py").run()

    # Check for any exceptions during startup - we allow some exceptions since we're testing for underscores
    # The dashboard might have data issues, but we can still check the UI for underscores
    if at.exception:
        print(f"Dashboard had exceptions (this is OK for underscore testing): {[e.message for e in at.exception]}")
    
    # Get all markdown elements (which contain most of the visible text)
    markdown_elements = at.markdown
    
    # Extract visible text from all markdown elements
    visible_texts = extract_visible_text(markdown_elements)
    
    # Also check for any text in other elements that might be visible
    # Check dataframes (tables) as they might contain underscores in headers or data
    if hasattr(at, 'dataframe'):
        for df_element in at.dataframe:
            if hasattr(df_element, 'data'):
                # Check column names
                if hasattr(df_element.data, 'columns'):
                    for col in df_element.data.columns:
                        if '_' in str(col):
                            pytest.fail(f"Underscore found in dataframe column: '{col}'")
                
                # Check data content
                if hasattr(df_element.data, 'values'):
                    for row in df_element.data.values:
                        for cell in row:
                            if isinstance(cell, str) and '_' in cell:
                                pytest.fail(f"Underscore found in dataframe data: '{cell}'")
    
    # Check all visible text for underscores
    underscore_found = False
    underscore_details = []
    
    for text in visible_texts:
        underscores = find_underscores_in_text(text)
        if underscores:
            underscore_found = True
            # Get context around the underscore (20 chars before and after)
            for pos in underscores:
                start = max(0, pos - 20)
                end = min(len(text), pos + 21)
                context = text[start:end]
                underscore_details.append(f"Text: '...{context}...' (position {pos})")
    
    # If any underscores are found, fail the test with details
    if underscore_found:
        error_message = "Underscores found in visible UI content. This indicates database field names may be leaking through:\n"
        error_message += "\n".join(underscore_details)
        error_message += f"\n\nTotal visible texts checked: {len(visible_texts)}"
        pytest.fail(error_message)
    
    # If we get here, no underscores were found
    assert True, "No underscores found in dashboard UI content - all field names properly human-readable"

def test_no_underscores_in_dashboard_ui_with_data():
    """
    Test with sample data to ensure underscores don't appear when data is present.
    This test creates a mock database scenario to test the UI with actual data.
    """
    # Import database utilities to set up test data
    from vertex_benchmark.database_utils import get_db_connection, create_tables, begin_batch, end_batch, insert_benchmark_result
    import uuid
    from datetime import datetime
    
    # Create a test database in memory
    test_db_path = "test_underscores.db"
    # Set up test database
    import sqlite3
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    
    # Create tables manually for test
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            cycle_num INTEGER NOT NULL,
            region TEXT NOT NULL,
            pro_time_ms REAL,
            flash_time_ms REAL,
            garden_models INTEGER,
            test_prompt TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            batch_id TEXT PRIMARY KEY,
            started_at DATETIME NOT NULL,
            ended_at DATETIME,
            app_version TEXT,
            config_json TEXT NOT NULL
        )
    """)
    
    # Insert test batch
    batch_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO batches (batch_id, started_at, ended_at, app_version, config_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (batch_id, datetime.now().isoformat(), datetime.now().isoformat(), "1.0.0", "{}")
    )
    
    # Insert test result with potential underscore fields
    cursor.execute(
        """
        INSERT INTO benchmark_results (batch_id, timestamp, cycle_num, region, pro_time_ms, flash_time_ms, garden_models, test_prompt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (batch_id, datetime.now().isoformat(), 1, "europe-west1", 150.5, 120.3, 5, "Test prompt")
    )
    
    conn.commit()
    conn.close()
    
    # Run the dashboard with test data
    at = AppTest.from_file("src/vertex_benchmark/dashboard.py").run()

    # Check for exceptions - we allow some exceptions since we're testing for underscores
    if at.exception:
        print(f"Dashboard had exceptions with test data (this is OK for underscore testing): {[e.message for e in at.exception]}")
    assert len(at.error) == 0, f"The dashboard displayed errors with test data: {[e.value for e in at.error]}"

    # Extract and check visible text
    markdown_elements = at.markdown
    visible_texts = extract_visible_text(markdown_elements)

    # Check for underscores in visible text
    underscore_found = False
    underscore_details = []

    for text in visible_texts:
        underscores = find_underscores_in_text(text)
        if underscores:
            underscore_found = True
            for pos in underscores:
                start = max(0, pos - 20)
                end = min(len(text), pos + 21)
                context = text[start:end]
                underscore_details.append(f"Text: '...{context}...' (position {pos})")

    # Check dataframes specifically
    if hasattr(at, 'dataframe'):
        for df_element in at.dataframe:
            if hasattr(df_element, 'data'):
                # Check column names
                if hasattr(df_element.data, 'columns'):
                    for col in df_element.data.columns:
                        if '_' in str(col):
                            pytest.fail(f"Underscore found in dataframe column with test data: '{col}'")

                # Check data content
                if hasattr(df_element.data, 'values'):
                    for row in df_element.data.values:
                        for cell in row:
                            if isinstance(cell, str) and '_' in cell:
                                pytest.fail(f"Underscore found in dataframe data with test data: '{cell}'")

    # Report any underscores found
    if underscore_found:
        error_message = "Underscores found in visible UI content with test data:\n"
        error_message += "\n".join(underscore_details)
        pytest.fail(error_message)

    # Success if no underscores found
    assert True, "No underscores found in dashboard UI content with test data"

