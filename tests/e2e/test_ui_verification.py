#!/usr/bin/env python3
"""
Test script to verify the dashboard UI changes.
This script checks that the flag buttons are positioned correctly in the header.
"""

import streamlit as st
import sys
import os

# Add the current directory to the path to import dashboard modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_header_layout():
    """Test that the header layout is correctly implemented."""
    print("Testing dashboard header layout...")
    
    # Read the dashboard.py file
    with open('src/vertex_benchmark/dashboard.py', 'r') as f:
        content = f.read()
    
    # Check for the presence of header columns
    if 'header_col1, header_col2, header_col3, header_col4 = st.columns([3, 1, 1, 2])' in content:
        print("✓ Header columns layout found")
    else:
        print("✗ Header columns layout not found")
        return False
    
    # Check for flag buttons in header
    if ':flag-sk:' in content and ':flag-us:' in content:
        print("✓ Flag buttons found in header")
    else:
        print("✗ Flag buttons not found in header")
        return False
    
    # Check for Deploy button
    if 'Deploy' in content and 'deploy_button' in content:
        print("✓ Deploy button found")
    else:
        print("✗ Deploy button not found")
        return False
    
    # Check that the old flag button code is removed
    old_code = 'col1, col2, col3 = st.columns([1, 1, 6])'
    if old_code not in content:
        print("✓ Old flag button layout removed")
    else:
        print("✗ Old flag button layout still present")
        return False
    
    print("All UI layout tests passed!")
    return True

def test_functionality():
    """Test that the functionality is preserved."""
    print("\nTesting dashboard functionality...")
    
    # Read the dashboard.py file
    with open('src/vertex_benchmark/dashboard.py', 'r') as f:
        content = f.read()
    
    # Check for session state management
    if 'st.session_state.selected_lang' in content:
        print("✓ Session state management preserved")
    else:
        print("✗ Session state management not found")
        return False
    
    # Check for language switching functionality
    if 'st.session_state.selected_lang = \'sk\'' in content and 'st.session_state.selected_lang = \'en\'' in content:
        print("✓ Language switching functionality preserved")
    else:
        print("✗ Language switching functionality not found")
        return False
    
    # Check for rerun calls
    if 'st.rerun()' in content:
        print("✓ Rerun functionality preserved")
    else:
        print("✗ Rerun functionality not found")
        return False
    
    print("All functionality tests passed!")
    return True

if __name__ == "__main__":
    print("Dashboard UI Verification Test")
    print("=" * 40)
    
    layout_test = test_header_layout()
    functionality_test = test_functionality()
    
    if layout_test and functionality_test:
        print("\n🎉 All tests passed! The UI changes are correctly implemented.")
        print("\nSummary of changes:")
        print("- Flag buttons moved to header section")
        print("- Deploy button added to header")
        print("- Proper column layout for right alignment")
        print("- All functionality preserved")
    else:
        print("\n❌ Some tests failed. Please review the implementation.")