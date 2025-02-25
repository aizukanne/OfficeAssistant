# Contributing Guidelines

## Overview
This document outlines the standards and practices for contributing to this project. All contributions must follow these guidelines to maintain code quality and consistency.

## Code Organization

### Directory Structure
```
src/
  ├── services/
  │   ├── __init__.py           # Only imports/exports
  │   ├── service_name/
  │   │   ├── __init__.py       # Public interface
  │   │   ├── service.py        # Service implementation
  │   │   ├── functions.py      # Public functions
  │   │   ├── service.pyi       # Type hint stubs
  │   │   └── constants.py      # Constants and configs
  └── interfaces/
      └── __init__.py           # All interfaces
```

### Function Implementation Pattern
```python
@log_function_call('service_name')
@with_error_recovery(
    operation=lambda *args, **kwargs: original_operation(*args, **kwargs),
    recovery=lambda *args, **kwargs: fallback_operation(*args, **kwargs)
)
def function_name(param: type) -> return_type:
    """
    Function description.
    
    Args:
        param: Parameter description
    
    Returns:
        Description of return value
    
    Raises:
        ErrorType: Error description
            Context includes:
            - key: value description
    
    Example:
        >>> result = function_name("test")
        >>> result["key"]
        'value'
    """
    try:
        service = get_instance()
        return service.operation(*args, **kwargs)
    except Exception as e:
        handle_service_error(
            'service_name',
            'operation_name',
            ErrorType,
            **context
        )(e)
```

## Logging Standards

### Function Logging
- Use @log_function_call decorator
- Include service name and operation
- Add performance metrics
- Provide operation context

### Error Logging
- Use log_error utility
- Include error type and details
- Preserve stack traces
- Add relevant context

### Log Format
```python
f"{timestamp} [{level}] [{service}] {message} {context}"
```

### Context Format
- Use key=value pairs
- Sort alphabetically
- Sanitize values
- Limit value length

## Error Handling

### Error Hierarchy
- Extend BaseError for all custom exceptions
- Use service-specific error types
- Include error context
- Preserve error chains

### Recovery Pattern
```python
@with_error_recovery(
    operation=lambda: original_operation(),
    recovery=lambda: fallback_operation()
)
def function_name():
    """Implementation with recovery."""
```

### Error Context
- Include operation details
- Add input parameters
- Track recovery attempts
- Monitor performance

### Resource Cleanup
- Use context managers
- Implement proper cleanup
- Handle cleanup errors
- Log cleanup status

## Documentation

### Docstring Format
```python
def function_name(param: type) -> return_type:
    """
    Concise description.
    
    Detailed description if needed.
    
    Args:
        param: Parameter description
            Additional details:
            - requirement 1
            - requirement 2
    
    Returns:
        return_type: Description of return value
            Contains:
            - key1 (type): description
            - key2 (type): description
    
    Raises:
        ErrorType: Error description
            Context includes:
            - key1: description
            - key2: description
    
    Example:
        >>> result = function_name("test")
        >>> result["key"]
        'value'
    """
```

### Type Hints
- Use .pyi stub files
- Specify all types
- Use Optional for optional params
- Document complex types

### Examples
- Include working examples
- Show error handling
- Demonstrate recovery
- Test all examples

## Testing Requirements

### Test Coverage
- Test all public functions
- Cover error scenarios
- Test recovery mechanisms
- Verify examples

### Test Pattern
```python
def test_function_success(mock_service):
    """Test successful operation."""
    result = function_name(param)
    assert expected_condition

def test_function_error(mock_service):
    """Test error handling."""
    with pytest.raises(ErrorType) as exc:
        function_name(param)
    assert error_context in exc.value.context

def test_function_recovery(mock_service):
    """Test recovery mechanism."""
    result = function_name(param)
    assert result == fallback_value
```

## Pull Request Process

1. Code Changes
   - Follow directory structure
   - Implement function patterns
   - Add proper error handling
   - Include documentation

2. Testing
   - Add comprehensive tests
   - Verify error handling
   - Test recovery mechanisms
   - Check documentation

3. Documentation
   - Update docstrings
   - Add type hints
   - Include examples
   - Update guides

4. Review Process
   - Code review
   - Documentation review
   - Test review
   - Performance review

## Version Control

### Commit Messages
```
type(scope): brief description

Detailed description of changes.

BREAKING CHANGE: description of breaking changes
```

### Types
- feat: New feature
- fix: Bug fix
- refactor: Code change
- docs: Documentation
- test: Test changes
- chore: Maintenance

## Review Checklist

- [ ] Follows directory structure
- [ ] Implements function patterns
- [ ] Includes proper logging
- [ ] Has error handling
- [ ] Contains recovery mechanisms
- [ ] Complete documentation
- [ ] Comprehensive tests
- [ ] Type hints added
- [ ] Examples included
- [ ] Performance considered