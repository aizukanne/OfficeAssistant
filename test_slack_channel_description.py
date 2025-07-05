#!/usr/bin/env python3
"""
Test script for the Slack channel description tool.
This script tests the new set_slack_channel_description function.
"""

import json
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tool_schema():
    """Test that the tool schema is properly defined."""
    try:
        from tools import tools
        
        # Find the new tool in the tools list
        channel_desc_tool = None
        for tool in tools:
            if tool.get('function', {}).get('name') == 'set_slack_channel_description':
                channel_desc_tool = tool
                break
        
        if not channel_desc_tool:
            print("❌ Tool schema not found in tools.py")
            return False
        
        # Validate schema structure
        function_def = channel_desc_tool['function']
        required_fields = ['name', 'description', 'parameters']
        
        for field in required_fields:
            if field not in function_def:
                print(f"❌ Missing required field '{field}' in tool schema")
                return False
        
        # Check parameters
        params = function_def['parameters']
        if 'channel' not in params['required']:
            print("❌ 'channel' parameter not marked as required")
            return False
        
        properties = params['properties']
        expected_props = ['channel', 'purpose', 'topic']
        for prop in expected_props:
            if prop not in properties:
                print(f"❌ Missing parameter '{prop}' in schema")
                return False
        
        print("✅ Tool schema validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing tool schema: {e}")
        return False

def test_function_import():
    """Test that the function can be imported."""
    try:
        from slack_integration import set_slack_channel_description, resolve_channel_to_id
        print("✅ Function import successful")
        return True
    except ImportError as e:
        print(f"❌ Function import failed: {e}")
        return False

def test_function_registration():
    """Test that the function is registered in lambda_function.py."""
    try:
        from lambda_function import get_available_functions
        
        # Test Slack functions
        slack_functions = get_available_functions('slack')
        
        if 'set_slack_channel_description' not in slack_functions:
            print("❌ Function not registered for Slack platform")
            return False
        
        print("✅ Function registration successful")
        return True
        
    except Exception as e:
        print(f"❌ Error testing function registration: {e}")
        return False

def test_function_logic():
    """Test the function logic with mock data."""
    try:
        from slack_integration import set_slack_channel_description
        
        # Test input validation
        result = set_slack_channel_description("test_channel")
        if not result.get('success') == False:
            print("❌ Input validation failed - should require purpose or topic")
            return False
        
        if "At least one of 'purpose' or 'topic' must be provided" not in result.get('error', ''):
            print("❌ Input validation error message incorrect")
            return False
        
        print("✅ Function logic validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing function logic: {e}")
        return False

def test_channel_resolution():
    """Test the channel resolution logic."""
    try:
        from slack_integration import resolve_channel_to_id
        
        # Test channel ID passthrough
        channel_id = "C1234567890"
        result = resolve_channel_to_id(channel_id)
        if result != channel_id:
            print("❌ Channel ID passthrough failed")
            return False
        
        print("✅ Channel resolution logic passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing channel resolution: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Slack Channel Description Tool Implementation")
    print("=" * 60)
    
    tests = [
        ("Tool Schema", test_tool_schema),
        ("Function Import", test_function_import),
        ("Function Registration", test_function_registration),
        ("Function Logic", test_function_logic),
        ("Channel Resolution", test_channel_resolution),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        if test_func():
            passed += 1
        else:
            print(f"   Test failed!")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The implementation is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())