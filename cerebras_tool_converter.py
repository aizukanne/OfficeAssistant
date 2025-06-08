import copy
import json

def convert_tools_for_cerebras(openai_tools):
    """
    Convert OpenAI-format tools to Cerebras-compatible format.
    
    Based on Cerebras documentation:
    - Supports basic JSON Schema 
    - Does NOT support union types like ["string", "null"]
    - Requires "strict": True in function schema (but this seems to be for structured outputs, not tools)
    - Uses standard OpenAI tool format
    
    Args:
        openai_tools (list): List of OpenAI-format tool definitions
        
    Returns:
        list: Cerebras-compatible tool definitions
    """
    
    def fix_json_schema_for_cerebras(schema):
        """
        Recursively fix JSON schema issues that Cerebras doesn't support
        """
        if isinstance(schema, dict):
            fixed_schema = {}
            for key, value in schema.items():
                if key == "type" and isinstance(value, list):
                    # Convert union types like ["string", "null"] to just the first non-null type
                    non_null_types = [t for t in value if t != "null"]
                    if non_null_types:
                        fixed_schema[key] = non_null_types[0]
                    else:
                        fixed_schema[key] = "string"  # fallback
                    print(f"    Fixed union type: {value} → {fixed_schema[key]}")
                else:
                    fixed_schema[key] = fix_json_schema_for_cerebras(value)
            return fixed_schema
        elif isinstance(schema, list):
            return [fix_json_schema_for_cerebras(item) for item in schema]
        else:
            return schema
    
    def remove_optional_from_required(parameters):
        """
        Remove fields that became optional (had null in union type) from required array
        """
        if not isinstance(parameters, dict):
            return parameters
            
        properties = parameters.get("properties", {})
        required = parameters.get("required", [])
        
        # Find fields that were union types with null (now optional)
        optional_fields = []
        for field_name, field_def in properties.items():
            # Check if this field was originally a union type with null
            # (This is hard to detect after conversion, so we'll be conservative)
            pass
        
        # For now, keep the required array as-is since we can't easily detect
        # which fields were originally optional
        return parameters
    
    try:
        #print("🔧 Converting tools for Cerebras compatibility...")
        
        # Deep copy to avoid modifying original tools
        cerebras_tools = copy.deepcopy(openai_tools)
        
        converted_count = 0
        for i, tool in enumerate(cerebras_tools):
            if tool.get("type") != "function":
                continue
                
            function_def = tool.get("function", {})
            function_name = function_def.get("name", f"tool_{i}")
            
            #print(f"  Converting tool: {function_name}")
            
            # Fix the parameters schema
            if "parameters" in function_def:
                original_params = function_def["parameters"]
                fixed_params = fix_json_schema_for_cerebras(original_params)
                function_def["parameters"] = fixed_params
                converted_count += 1
            
            # Ensure function has required fields
            if not function_def.get("name"):
                print(f"    Warning: Tool missing name, skipping")
                continue
                
            if not function_def.get("description"):
                print(f"    Warning: Tool {function_name} missing description")
                function_def["description"] = f"Function {function_name}"
        
        #print(f"✅ Successfully converted {converted_count} tools for Cerebras")
        
        # Validate the result
        validation_errors = validate_cerebras_tools(cerebras_tools)
        if validation_errors:
            print("⚠️ Validation warnings:")
            for error in validation_errors:
                print(f"    {error}")
        
        #print(json.dumps(cerebras_tools))
        return cerebras_tools
        
    except Exception as e:
        print(f"❌ Error converting tools: {e}")
        return []


def validate_cerebras_tools(tools):
    """
    Validate that tools meet Cerebras requirements
    
    Returns:
        list: List of validation error messages (empty if valid)
    """
    errors = []
    
    for i, tool in enumerate(tools):
        if not isinstance(tool, dict):
            errors.append(f"Tool {i}: Not a dictionary")
            continue
            
        if tool.get("type") != "function":
            errors.append(f"Tool {i}: Type must be 'function'")
            continue
            
        function = tool.get("function", {})
        if not isinstance(function, dict):
            errors.append(f"Tool {i}: Function must be a dictionary")
            continue
            
        # Check required fields
        if not function.get("name"):
            errors.append(f"Tool {i}: Missing function name")
            
        if not function.get("description"):
            errors.append(f"Tool {i}: Missing function description")
            
        # Check parameters schema
        parameters = function.get("parameters", {})
        if parameters:
            # Check for unsupported union types
            param_str = json.dumps(parameters)
            if '"type":[' in param_str.replace(' ', ''):
                errors.append(f"Tool {i}: Contains union types in parameters")
    
    return errors

def test_conversion():
    """
    Test the conversion with sample tools that have union types
    """
    print("🧪 Testing tool conversion...")
    
    # Sample tools with union types (like yours)
    test_tools = [
        {
            "type": "function",
            "function": {
                "name": "test_function",
                "description": "A test function",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "required_field": {
                            "type": "string",
                            "description": "A required string field"
                        },
                        "optional_field": {
                            "type": ["string", "null"],
                            "description": "An optional string field"
                        },
                        "optional_bool": {
                            "type": ["boolean", "null"],
                            "description": "An optional boolean field"
                        }
                    },
                    "required": ["required_field"]
                }
            }
        }
    ]
    
    print("Original tools:")
    print(json.dumps(test_tools, indent=2))
    
    converted = convert_tools_for_cerebras(test_tools)
    
    print("\nConverted tools:")
    print(json.dumps(converted, indent=2))
    
    return converted

if __name__ == "__main__":
    # Run test
    test_conversion()