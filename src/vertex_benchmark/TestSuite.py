#!/usr/bin/env python3
"""
Simple test runner for the Vertex AI Performance Benchmarking project.
This script uses pytest to run all tests in the /tests directory.
"""

import subprocess
import sys
import os

def run_tests():
    """
    Runs all tests using pytest.
    Returns the exit code from pytest.
    """
    try:
        # Ensure we're in the correct directory
        os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        
        # Run pytest on the tests directory
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short"
        ], check=False)
        
        return result.returncode
        
    except FileNotFoundError:
        print("Error: pytest is not installed. Please install it with: pip install pytest")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def main():
    """
    Main function to run the test suite.
    """
    print("🚀 Running Vertex AI Benchmarking Test Suite")
    print("=" * 50)
    
    exit_code = run_tests()
    
    print("\n" + "=" * 50)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed with exit code: {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)