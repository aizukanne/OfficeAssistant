"""Test validation utilities."""
import inspect
import importlib
import coverage
from typing import Any, Dict, List, Set, Optional
from unittest.mock import MagicMock

def validate_test_names(module: Any) -> List[str]:
    """
    Validate test naming conventions.
    
    Args:
        module: Module to validate
        
    Returns:
        List[str]: List of issues found
        
    Example:
        >>> def test_without_doc(): pass
        >>> issues = validate_test_names(test_without_doc)
        >>> 'missing docstring' in issues[0]
        True
    """
    issues = []
    for name, obj in inspect.getmembers(module):
        if name.startswith('test_'):
            if not obj.__doc__:
                issues.append(f"{name}: missing docstring")
            elif len(obj.__doc__.split()) < 3:
                issues.append(f"{name}: docstring too short")
            if not name.lower() == name:
                issues.append(f"{name}: should be lowercase")
    return issues

def validate_test_coverage(module_path: str) -> Dict[str, float]:
    """
    Validate test coverage for module.
    
    Args:
        module_path: Path to module
        
    Returns:
        Dict[str, float]: Coverage metrics
        
    Example:
        >>> metrics = validate_test_coverage('src.utils.logging')
        >>> 'line_coverage' in metrics
        True
    """
    cov = coverage.Coverage()
    cov.start()
    importlib.import_module(module_path)
    cov.stop()
    
    _, lines, _, missing, _ = cov.analysis(module_path)
    total_lines = len(lines)
    covered_lines = total_lines - len(missing)
    
    return {
        'line_coverage': (covered_lines / total_lines) * 100 if total_lines else 0,
        'total_lines': total_lines,
        'covered_lines': covered_lines,
        'missing_lines': missing
    }

def validate_mock_usage(
    mock: MagicMock,
    expected_calls: List[str]
) -> List[str]:
    """
    Validate mock was used correctly.
    
    Args:
        mock: Mock to validate
        expected_calls: List of expected method calls
        
    Returns:
        List[str]: List of missing calls
        
    Example:
        >>> mock = MagicMock()
        >>> mock.test()
        >>> missing = validate_mock_usage(mock, ['test', 'other'])
        >>> missing == ['other']
        True
    """
    missing_calls = []
    for call in expected_calls:
        if not getattr(mock, call).called:
            missing_calls.append(call)
    return missing_calls

def validate_test_isolation(test_func: Any) -> List[str]:
    """
    Validate test isolation and fixture usage.
    
    Args:
        test_func: Test function to validate
        
    Returns:
        List[str]: List of issues found
        
    Example:
        >>> def test_func(mock_service): pass
        >>> issues = validate_test_isolation(test_func)
        >>> len(issues) == 0
        True
    """
    issues = []
    
    # Check fixture usage
    sig = inspect.signature(test_func)
    for param in sig.parameters.values():
        if not param.name.startswith(('mock_', 'test_')):
            issues.append(f"Parameter {param.name} should use mock or test fixtures")
    
    # Check for global state modifications
    source = inspect.getsource(test_func)
    if 'global ' in source:
        issues.append("Test modifies global state")
    
    return issues

def validate_test_structure(test_class: Any) -> List[str]:
    """
    Validate test class structure and organization.
    
    Args:
        test_class: Test class to validate
        
    Returns:
        List[str]: List of issues found
        
    Example:
        >>> class TestExample:
        ...     def test_method(self): pass
        >>> issues = validate_test_structure(TestExample)
        >>> len(issues) == 0
        True
    """
    issues = []
    
    # Check class naming
    if not test_class.__name__.startswith('Test'):
        issues.append("Class name should start with 'Test'")
    
    # Check method organization
    setup_found = False
    teardown_found = False
    
    for name, method in inspect.getmembers(test_class, predicate=inspect.isfunction):
        if name == 'setUp' or name == 'setup_method':
            setup_found = True
        elif name == 'tearDown' or name == 'teardown_method':
            teardown_found = True
        elif name.startswith('test_'):
            if not method.__doc__:
                issues.append(f"Method {name} missing docstring")
    
    if not setup_found and not teardown_found:
        issues.append("Missing setup/teardown methods")
    
    return issues

def validate_test_dependencies(test_module: Any) -> Set[str]:
    """
    Validate test dependencies and imports.
    
    Args:
        test_module: Test module to validate
        
    Returns:
        Set[str]: Set of external dependencies
        
    Example:
        >>> import pytest
        >>> deps = validate_test_dependencies(pytest)
        >>> len(deps) > 0
        True
    """
    dependencies = set()
    
    # Get all imports
    source = inspect.getsource(test_module)
    import_lines = [
        line.strip()
        for line in source.split('\n')
        if line.strip().startswith(('import ', 'from '))
    ]
    
    # Extract package names
    for line in import_lines:
        if line.startswith('import '):
            package = line.split()[1].split('.')[0]
            dependencies.add(package)
        elif line.startswith('from '):
            package = line.split()[1].split('.')[0]
            dependencies.add(package)
    
    return dependencies

def validate_test_performance(
    test_func: Any,
    max_duration: float = 1.0
) -> Dict[str, Any]:
    """
    Validate test performance.
    
    Args:
        test_func: Test function to validate
        max_duration: Maximum allowed duration in seconds
        
    Returns:
        Dict[str, Any]: Performance metrics
        
    Example:
        >>> def test_fast(): pass
        >>> metrics = validate_test_performance(test_fast)
        >>> metrics['passed']
        True
    """
    import time
    
    start_time = time.time()
    test_func()
    duration = time.time() - start_time
    
    return {
        'duration': duration,
        'passed': duration <= max_duration,
        'max_duration': max_duration
    }

def validate_test_fixtures(
    fixtures_module: Any,
    required_fixtures: Optional[List[str]] = None
) -> List[str]:
    """
    Validate test fixtures.
    
    Args:
        fixtures_module: Module containing fixtures
        required_fixtures: List of required fixture names
        
    Returns:
        List[str]: List of missing fixtures
        
    Example:
        >>> def mock_service(): pass
        >>> missing = validate_test_fixtures(mock_service, ['mock_service'])
        >>> len(missing) == 0
        True
    """
    if required_fixtures is None:
        required_fixtures = [
            'mock_storage_service',
            'mock_slack_service',
            'mock_openai_service',
            'mock_odoo_service',
            'mock_external_service'
        ]
    
    missing_fixtures = []
    
    for fixture in required_fixtures:
        if not hasattr(fixtures_module, fixture):
            missing_fixtures.append(fixture)
    
    return missing_fixtures