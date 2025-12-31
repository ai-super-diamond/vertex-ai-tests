import sys
import os
import pytest
from streamlit.testing.v1 import AppTest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_dashboard_runs_without_error():
    """Test that the dashboard runs without any exceptions or displayed errors."""
    at = AppTest.from_file("src/vertex_benchmark/dashboard.py").run()
    assert not at.exception, "The dashboard raised an exception during startup."
    assert len(at.error) == 0, f"The dashboard displayed the following errors: {[e.value for e in at.error]}"