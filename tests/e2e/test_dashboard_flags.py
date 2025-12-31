#!/usr/bin/env python3
"""
Test script to verify the dashboard flag button functionality
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, '.')

def test_dashboard_flag_functionality():
    """Test that the dashboard has the correct flag button implementation."""
    print("Testing dashboard flag button implementation...")
    
    try:
        # Read the dashboard.py file
        with open('dashboard.py', 'r') as f:
            dashboard_content = f.read()
        
        # Check for required imports
        required_imports = [
            'from PIL import Image',
            'import base64'
        ]
        
        for import_stmt in required_imports:
            if import_stmt not in dashboard_content:
                print(f"❌ Missing import: {import_stmt}")
                return False
            else:
                print(f"✅ Found import: {import_stmt}")
        
        # Check for flag image loading
        if 'Image.open("resources/us-flag.png")' not in dashboard_content:
            print("❌ US flag image loading not found")
            return False
        else:
            print("✅ US flag image loading found")
        
        if 'Image.open("resources/sk-flag.png")' not in dashboard_content:
            print("❌ Slovak flag image loading not found")
            return False
        else:
            print("✅ Slovak flag image loading found")
        
        # Check for image resizing
        if 'us_flag_img.resize((30, 20))' not in dashboard_content:
            print("❌ US flag image resizing not found")
            return False
        else:
            print("✅ US flag image resizing found")
        
        if 'sk_flag_img.resize((30, 20))' not in dashboard_content:
            print("❌ Slovak flag image resizing not found")
            return False
        else:
            print("✅ Slovak flag image resizing found")
        
        # Check for flag buttons
        if 'st.button(sk_flag_img, key="sk_flag"' not in dashboard_content:
            print("❌ Slovak flag button not found")
            return False
        else:
            print("✅ Slovak flag button found")
        
        if 'st.button(us_flag_img, key="us_flag"' not in dashboard_content:
            print("❌ US flag button not found")
            return False
        else:
            print("✅ US flag button found")
        
        # Check for language switching logic
        if 'st.session_state.selected_lang = \'sk\'' not in dashboard_content:
            print("❌ Slovak language switching not found")
            return False
        else:
            print("✅ Slovak language switching found")
        
        if 'st.session_state.selected_lang = \'en\'' not in dashboard_content:
            print("❌ English language switching not found")
            return False
        else:
            print("✅ English language switching found")
        
        # Check that the manual Deploy button was removed
        if 'st.button("Deploy", key="deploy_button")' in dashboard_content:
            print("❌ Manual Deploy button still exists (should be removed)")
            return False
        else:
            print("✅ Manual Deploy button correctly removed")
        
        # Check for CSS styling
        if '.flag-button' in dashboard_content:
            print("✅ Flag button CSS styling found")
        else:
            print("❌ Flag button CSS styling not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading dashboard.py: {e}")
        return False

def test_flag_image_files():
    """Test that flag image files exist and are accessible."""
    print("\nTesting flag image files...")
    
    flag_files = [
        ('resources/us-flag.png', 'US Flag'),
        ('resources/sk-flag.png', 'Slovak Flag')
    ]
    
    for file_path, description in flag_files:
        if os.path.exists(file_path):
            try:
                # Try to open the image
                from PIL import Image
                img = Image.open(file_path)
                print(f"✅ {description}: {file_path} ({img.size[0]}x{img.size[1]}px)")
            except Exception as e:
                print(f"❌ {description}: {file_path} (Error loading: {e})")
                return False
        else:
            print(f"❌ {description}: {file_path} (File not found)")
            return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Dashboard Flag Button Test Suite")
    print("=" * 60)
    
    # Test flag image files
    files_test_passed = test_flag_image_files()
    
    # Test dashboard implementation
    dashboard_test_passed = test_dashboard_flag_functionality()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    if files_test_passed and dashboard_test_passed:
        print("✅ All tests passed! The dashboard flag buttons are correctly implemented.")
        print("\nKey features verified:")
        print("- Flag images are loaded from resources directory")
        print("- Images are resized to 30x20 pixels for buttons")
        print("- Flag buttons trigger language switching")
        print("- Manual Deploy button has been removed")
        print("- CSS styling is applied to flag buttons")
        print("- Language switching updates session state")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)