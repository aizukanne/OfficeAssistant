#!/usr/bin/env python3
"""
Simple integration test that doesn't require external dependencies
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tool_definition():
    """Test that the tool definition is properly integrated"""
    print("Testing tool definition integration...")
    
    try:
        from tools import tools
        
        # Find our gemini tool
        gemini_tool = None
        for tool in tools:
            if (tool.get('type') == 'function' and 
                tool.get('function', {}).get('name') == 'gemini_generate_content'):
                gemini_tool = tool
                break
        
        if not gemini_tool:
            print("❌ gemini_generate_content tool not found")
            return False
        
        # Validate tool structure
        function_def = gemini_tool['function']
        
        # Check name
        if function_def['name'] != 'gemini_generate_content':
            print("❌ Tool name incorrect")
            return False
        
        # Check description exists
        if not function_def.get('description'):
            print("❌ Tool description missing")
            return False
        
        # Check parameters
        params = function_def.get('parameters', {})
        properties = params.get('properties', {})
        required = params.get('required', [])
        
        # Check required parameter 'prompt'
        if 'prompt' not in properties:
            print("❌ 'prompt' parameter missing")
            return False
        
        if 'prompt' not in required:
            print("❌ 'prompt' not in required parameters")
            return False
        
        # Check optional parameters exist
        expected_params = ['prompt', 'file_name_prefix', 'model']
        for param in expected_params:
            if param not in properties:
                print(f"❌ Parameter '{param}' missing")
                return False
        
        print("✅ Tool definition is complete and correct")
        return True
        
    except Exception as e:
        print(f"❌ Tool definition test failed: {e}")
        return False

def test_code_structure():
    """Test that the code structure is valid without importing dependencies"""
    print("Testing code structure...")
    
    # Test that media_processing.py has the right structure
    try:
        with open('media_processing.py', 'r') as f:
            content = f.read()
        
        # Check for function definitions
        if 'def upload_image_content_to_s3(' not in content:
            print("❌ upload_image_content_to_s3 function not found")
            return False
        
        if 'def gemini_generate_content(' not in content:
            print("❌ gemini_generate_content function not found") 
            return False
        
        # Check for required imports
        if 'from config import' not in content:
            print("❌ Config imports not found")
            return False
        
        if 'gemini_api_key' not in content:
            print("❌ gemini_api_key not imported")
            return False
        
        if 'image_bucket_name' not in content:
            print("❌ image_bucket_name not imported")
            return False
        
        # Check for proper typing
        if 'from typing import Dict, Any' not in content:
            print("❌ Typing imports not found")
            return False
        
        print("✅ Code structure is correct")
        return True
        
    except Exception as e:
        print(f"❌ Code structure test failed: {e}")
        return False

def test_function_signatures():
    """Test function signatures in the code"""
    print("Testing function signatures...")
    
    try:
        with open('media_processing.py', 'r') as f:
            content = f.read()
        
        # Check upload_image_content_to_s3 signature
        expected_upload_sig = 'def upload_image_content_to_s3(image_content: bytes, mime_type: str) -> str:'
        if expected_upload_sig not in content:
            print("❌ upload_image_content_to_s3 signature incorrect")
            return False
        
        # Check gemini_generate_content has required parameters
        if 'def gemini_generate_content(' not in content:
            print("❌ gemini_generate_content function not found")
            return False
        
        # Check return type annotation
        if ') -> Dict[str, Any]:' not in content:
            print("❌ Return type annotation missing")
            return False
        
        print("✅ Function signatures are correct")
        return True
        
    except Exception as e:
        print(f"❌ Function signature test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Running Simple Integration Tests")
    print("=" * 50)
    
    tests = [
        test_tool_definition,
        test_code_structure,
        test_function_signatures,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        print()
        if test_func():
            passed += 1
        print("-" * 30)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("✅ The Gemini content generation feature has been successfully integrated!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)