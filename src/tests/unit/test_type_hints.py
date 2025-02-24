"""Tests for type hint validation."""
import os
import pytest
import mypy.api
from typing import List, Dict, Any

def run_mypy(files: List[str]) -> Dict[str, Any]:
    """
    Run mypy on specified files.
    
    Args:
        files: List of files to check
        
    Returns:
        Dict[str, Any]: Results containing:
            - success (bool): Whether all checks passed
            - errors (List[str]): List of errors if any
            - count (int): Number of errors
    """
    # Construct mypy command
    command = [
        '--python-version=3.8',
        '--strict',
        '--show-error-codes',
        '--show-column-numbers',
        '--pretty'
    ]
    command.extend(files)
    
    # Run mypy
    stdout, stderr, exit_code = mypy.api.run(command)
    
    # Parse results
    errors = []
    if stdout:
        errors = [line for line in stdout.split('\n') if line.strip()]
    
    return {
        'success': exit_code == 0,
        'errors': errors,
        'count': len(errors)
    }

def test_storage_service_types():
    """Test storage service type hints."""
    files = [
        'src/services/storage/service.py',
        'src/services/storage/service.pyi',
        'src/services/storage/functions.py'
    ]
    result = run_mypy(files)
    assert result['success'], f"Type errors found:\n" + "\n".join(result['errors'])

def test_slack_service_types():
    """Test Slack service type hints."""
    files = [
        'src/services/slack/service.py',
        'src/services/slack/service.pyi'
    ]
    result = run_mypy(files)
    assert result['success'], f"Type errors found:\n" + "\n".join(result['errors'])

def test_openai_service_types():
    """Test OpenAI service type hints."""
    files = [
        'src/services/openai/service.py',
        'src/services/openai/service.pyi'
    ]
    result = run_mypy(files)
    assert result['success'], f"Type errors found:\n" + "\n".join(result['errors'])

def test_external_service_types():
    """Test external service type hints."""
    files = [
        'src/services/external/service.py',
        'src/services/external/service.pyi'
    ]
    result = run_mypy(files)
    assert result['success'], f"Type errors found:\n" + "\n".join(result['errors'])

def test_utility_types():
    """Test utility module type hints."""
    files = [
        'src/utils/logging.py',
        'src/utils/decorators.py',
        'src/utils/error_handling.py',
        'src/utils/docstring.py'
    ]
    result = run_mypy(files)
    assert result['success'], f"Type errors found:\n" + "\n".join(result['errors'])

def test_interface_types():
    """Test interface type hints."""
    files = [
        'src/interfaces/__init__.py'
    ]
    result = run_mypy(files)
    assert result['success'], f"Type errors found:\n" + "\n".join(result['errors'])

def test_core_types():
    """Test core module type hints."""
    files = [
        'src/core/exceptions.py'
    ]
    result = run_mypy(files)
    assert result['success'], f"Type errors found:\n" + "\n".join(result['errors'])

def test_all_type_hints():
    """Test all type hints in project."""
    # Get all Python files
    python_files = []
    for root, _, files in os.walk('src'):
        for file in files:
            if file.endswith(('.py', '.pyi')):
                python_files.append(os.path.join(root, file))
    
    result = run_mypy(python_files)
    assert result['success'], f"Type errors found:\n" + "\n".join(result['errors'])

def test_stub_completeness():
    """Test that all services have stub files."""
    services = [
        'storage',
        'slack',
        'openai',
        'external'
    ]
    
    for service in services:
        stub_file = f'src/services/{service}/service.pyi'
        assert os.path.exists(stub_file), f"Missing stub file: {stub_file}"

def test_stub_consistency():
    """Test that stubs match implementations."""
    def get_public_members(file_path: str) -> List[str]:
        """Get public members from a file."""
        import ast
        with open(file_path) as f:
            tree = ast.parse(f.read())
        
        members = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not node.name.startswith('_'):
                    members.append(node.name)
        return sorted(members)
    
    services = [
        'storage',
        'slack',
        'openai',
        'external'
    ]
    
    for service in services:
        impl_file = f'src/services/{service}/service.py'
        stub_file = f'src/services/{service}/service.pyi'
        
        impl_members = get_public_members(impl_file)
        stub_members = get_public_members(stub_file)
        
        assert impl_members == stub_members, \
            f"Mismatch in {service} service:\n" \
            f"Implementation: {impl_members}\n" \
            f"Stub: {stub_members}"