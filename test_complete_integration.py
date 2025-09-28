#!/usr/bin/env python3
"""
Complete integration test for Gemini content generation
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tool_definition():
    """Test that the tool definition exists"""
    print("1. Testing tool definition...")
    try:
        from tools import tools
        
        gemini_tool = None
        for tool in tools:
            if (tool.get('type') == 'function' and 
                tool.get('function', {}).get('name') == 'gemini_generate_content'):
                gemini_tool = tool
                break
        
        if gemini_tool:
            print("   ✅ Tool definition found in tools.py")
            return True
        else:
            print("   ❌ Tool definition not found in tools.py")
            return False
    except Exception as e:
        print(f"   ❌ Tool definition test failed: {e}")
        return False

def test_function_import():
    """Test that the function can be imported"""
    print("2. Testing function import...")
    try:
        # Test direct import
        from media_processing import gemini_generate_content
        print("   ✅ Function can be imported from media_processing")
        
        # Test lambda_function import
        from lambda_function import gemini_generate_content as lambda_imported
        print("   ✅ Function can be imported from lambda_function")
        
        # Verify they're the same function
        if gemini_generate_content is lambda_imported:
            print("   ✅ Function objects are identical")
            return True
        else:
            print("   ❌ Function objects are different")
            return False
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_available_functions_mapping():
    """Test that the function is in the available functions"""
    print("3. Testing available functions mapping...")
    try:
        from lambda_function import get_available_functions
        
        # Test for all platforms
        platforms = ['slack', 'telegram', 'unknown']
        for platform in platforms:
            available = get_available_functions(platform)
            if 'gemini_generate_content' in available:
                print(f"   ✅ Function available for platform '{platform}'")
            else:
                print(f"   ❌ Function NOT available for platform '{platform}'")
                return False
        
        return True
    except Exception as e:
        print(f"   ❌ Available functions test failed: {e}")
        return False

def test_cerebras_tool_filtering():
    """Test that the function is in Cerebras tool selection"""
    print("4. Testing Cerebras tool filtering...")
    try:
        from conversation import select_cerebras_tools
        from tools import tools
        
        cerebras_tools = select_cerebras_tools(tools)
        
        # Check if our tool is included
        gemini_found = False
        for tool in cerebras_tools:
            if tool.get('function', {}).get('name') == 'gemini_generate_content':
                gemini_found = True
                break
        
        if gemini_found:
            print("   ✅ Function included in Cerebras tool selection")
            return True
        else:
            print("   ❌ Function NOT included in Cerebras tool selection")
            return False
    except Exception as e:
        print(f"   ❌ Cerebras tool filtering test failed: {e}")
        return False

def test_function_signature():
    """Test function signature and return structure"""
    print("5. Testing function signature...")
    try:
        from media_processing import gemini_generate_content
        import inspect
        
        sig = inspect.signature(gemini_generate_content)
        params = list(sig.parameters.keys())
        
        expected_params = ['prompt', 'file_name_prefix', 'model']
        if params == expected_params:
            print("   ✅ Function signature is correct")
        else:
            print(f"   ❌ Function signature mismatch. Expected: {expected_params}, Got: {params}")
            return False
        
        # Test default values
        param_defaults = {
            name: param.default 
            for name, param in sig.parameters.items() 
            if param.default is not param.empty
        }
        
        expected_defaults = {
            'file_name_prefix': 'generated_content',
            'model': 'gemini-2.5-flash-image-preview'
        }
        
        if param_defaults == expected_defaults:
            print("   ✅ Default parameter values are correct")
            return True
        else:
            print(f"   ❌ Default values mismatch. Expected: {expected_defaults}, Got: {param_defaults}")
            return False
    except Exception as e:
        print(f"   ❌ Function signature test failed: {e}")
        return False

def test_code_integration():
    """Test that all required code pieces are in place"""
    print("6. Testing code integration...")
    
    tests_passed = 0
    total_tests = 0
    
    # Check media_processing.py
    total_tests += 1
    try:
        with open('media_processing.py', 'r') as f:
            content = f.read()
        
        required_elements = [
            'def gemini_generate_content(',
            'def upload_image_content_to_s3(',
            'from config import',
            'gemini_api_key',
            'image_bucket_name',
            'from typing import Dict, Any'
        ]
        
        all_found = all(element in content for element in required_elements)
        if all_found:
            print("   ✅ media_processing.py contains all required elements")
            tests_passed += 1
        else:
            missing = [elem for elem in required_elements if elem not in content]
            print(f"   ❌ media_processing.py missing: {missing}")
    except Exception as e:
        print(f"   ❌ media_processing.py test failed: {e}")
    
    # Check lambda_function.py
    total_tests += 1
    try:
        with open('lambda_function.py', 'r') as f:
            content = f.read()
        
        required_elements = [
            'gemini_generate_content',  # In import
            '"gemini_generate_content": gemini_generate_content'  # In mapping
        ]
        
        all_found = all(element in content for element in required_elements)
        if all_found:
            print("   ✅ lambda_function.py contains all required elements")
            tests_passed += 1
        else:
            missing = [elem for elem in required_elements if elem not in content]
            print(f"   ❌ lambda_function.py missing: {missing}")
    except Exception as e:
        print(f"   ❌ lambda_function.py test failed: {e}")
    
    # Check conversation.py
    total_tests += 1
    try:
        with open('conversation.py', 'r') as f:
            content = f.read()
        
        if '"gemini_generate_content"' in content:
            print("   ✅ conversation.py contains tool name in Cerebras filter")
            tests_passed += 1
        else:
            print("   ❌ conversation.py missing gemini_generate_content in Cerebras filter")
    except Exception as e:
        print(f"   ❌ conversation.py test failed: {e}")
    
    return tests_passed == total_tests

def main():
    """Run all integration tests"""
    print("🔧 Running Complete Integration Tests")
    print("=" * 60)
    
    tests = [
        test_tool_definition,
        test_function_import,
        test_available_functions_mapping,
        test_cerebras_tool_filtering,
        test_function_signature,
        test_code_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        print()
        if test_func():
            passed += 1
        print("-" * 40)
    
    print(f"\n📊 Final Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ The Gemini content generation feature is FULLY integrated!")
        print("\n📋 Integration Summary:")
        print("   • Function implemented in media_processing.py")
        print("   • Tool schema added to tools.py")
        print("   • Function imported in lambda_function.py")
        print("   • Function mapped in get_available_functions()")
        print("   • Function allowlisted for Cerebras in conversation.py")
        print("\n🚀 The feature is ready for production use!")
        return True
    else:
        print("\n⚠️  Some integration tests failed.")
        print("Please review the output above and fix the issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)