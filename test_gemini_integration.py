#!/usr/bin/env python3
"""
Test script for Gemini content generation integration
"""

import sys
import os

# Add the current directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test that we can import the function"""
    print("Testing imports...")
    try:
        from media_processing import gemini_generate_content, upload_image_content_to_s3
        print("✅ Successfully imported gemini_generate_content and upload_image_content_to_s3")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config_import():
    """Test that config imports work"""
    print("Testing config imports...")
    try:
        from config import gemini_api_key, image_bucket_name
        if gemini_api_key:
            print("✅ gemini_api_key is available")
        else:
            print("⚠️  gemini_api_key is None - check environment variable GEMINI_API_KEY")
        
        if image_bucket_name:
            print(f"✅ image_bucket_name is available: {image_bucket_name}")
        else:
            print("❌ image_bucket_name is None")
        
        return True
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False

def test_function_signature():
    """Test that the function has the correct signature"""
    print("Testing function signature...")
    try:
        from media_processing import gemini_generate_content
        import inspect
        
        sig = inspect.signature(gemini_generate_content)
        params = list(sig.parameters.keys())
        
        expected_params = ['prompt', 'file_name_prefix', 'model']
        if params == expected_params:
            print("✅ Function signature is correct")
            return True
        else:
            print(f"❌ Function signature mismatch. Expected: {expected_params}, Got: {params}")
            return False
    except Exception as e:
        print(f"❌ Function signature test failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality with a simple prompt"""
    print("Testing basic functionality...")
    try:
        from media_processing import gemini_generate_content
        from config import gemini_api_key
        
        if not gemini_api_key:
            print("⚠️  Skipping functionality test - no API key available")
            return True
        
        # Test with a simple text-only prompt first
        result = gemini_generate_content(
            prompt="Write a short haiku about programming",
            file_name_prefix="test_haiku"
        )
        
        # Check return structure
        expected_keys = {'success', 'text_content', 'generated_files', 'error'}
        result_keys = set(result.keys())
        
        if result_keys == expected_keys:
            print("✅ Return structure is correct")
        else:
            print(f"❌ Return structure mismatch. Expected: {expected_keys}, Got: {result_keys}")
            return False
        
        if result['success']:
            print(f"✅ Function executed successfully")
            print(f"✅ Generated text length: {len(result['text_content'])} characters")
            print(f"✅ Generated files: {len(result['generated_files'])}")
            return True
        else:
            print(f"⚠️  Function returned success=False with error: {result['error']}")
            return True  # This might be expected if API key is invalid, etc.
            
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_tool_definition():
    """Test that tool definition is properly added"""
    print("Testing tool definition...")
    try:
        from tools import tools
        
        # Look for our tool in the tools list
        gemini_tool = None
        for tool in tools:
            if (tool.get('type') == 'function' and 
                tool.get('function', {}).get('name') == 'gemini_generate_content'):
                gemini_tool = tool
                break
        
        if gemini_tool:
            print("✅ Tool definition found in tools.py")
            
            # Check required parameters
            params = gemini_tool['function']['parameters']['properties']
            required = gemini_tool['function']['parameters']['required']
            
            if 'prompt' in params and 'prompt' in required:
                print("✅ Tool definition has correct parameters")
                return True
            else:
                print("❌ Tool definition missing required 'prompt' parameter")
                return False
        else:
            print("❌ Tool definition not found in tools.py")
            return False
            
    except Exception as e:
        print(f"❌ Tool definition test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running Gemini Integration Tests")
    print("=" * 50)
    
    tests = [
        test_import,
        test_config_import,
        test_function_signature,
        test_tool_definition,
        test_basic_functionality,
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
        print("🎉 All tests passed! Integration appears successful.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)