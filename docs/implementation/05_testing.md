# Phase 5: Testing Implementation

## Objective
Standardize testing across all services, ensuring comprehensive coverage, consistent mocking, and proper test organization.

## Prerequisites
- Phase 1 (Code Organization) completed
- Phase 2 (Logging) completed
- Phase 3 (Error Handling) completed
- Phase 4 (Documentation) completed

## Current Issues
1. Inconsistent mock usage
2. Mixed unit/integration tests
3. Missing test cases
4. Incomplete coverage

## Implementation Steps

### 1. Define Test Structure
```
tests/
  ├── unit/
  │   ├── services/
  │   │   ├── test_storage_service.py
  │   │   ├── test_slack_service.py
  │   │   └── ...
  │   ├── utils/
  │   │   └── test_logging.py
  │   └── conftest.py
  ├── integration/
  │   ├── services/
  │   │   └── test_service_integration.py
  │   └── conftest.py
  └── fixtures/
      ├── data/
      │   └── test_files/
      └── mocks/
          └── aws/
```

### 2. Create Test Utilities
```python
# tests/utils/test_utils.py
import pytest
from typing import Any, Callable, Dict, Type
from unittest.mock import MagicMock

def create_service_mock(
    service_class: Type[Any],
    **method_returns: Any
) -> MagicMock:
    """
    Create a standardized service mock.
    
    Args:
        service_class: Service class to mock
        **method_returns: Return values for specific methods
    
    Returns:
        MagicMock: Configured service mock
    """
    mock = MagicMock(spec=service_class)
    for method, return_value in method_returns.items():
        setattr(mock, method, MagicMock(return_value=return_value))
    return mock

def async_test(coro: Callable) -> Callable:
    """Decorator for async test functions."""
    import asyncio
    
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(coro(*args, **kwargs))
    return wrapper
```

### 3. Implement Standard Fixtures
```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock
from src.services.storage_service import StorageService

@pytest.fixture
def mock_s3():
    """Create mock S3 client."""
    mock = MagicMock()
    mock.upload_fileobj.return_value = None
    mock.download_fileobj.return_value = None
    return mock

@pytest.fixture
def mock_storage_service(mock_s3):
    """Create mock storage service."""
    service = MagicMock(spec=StorageService)
    service.s3_client = mock_s3
    return service

@pytest.fixture
def test_data():
    """Provide test data."""
    return {
        'id': 'test-123',
        'content': 'test content',
        'metadata': {'type': 'test'}
    }
```

### 4. Update Service Tests
```python
# tests/unit/services/test_storage_service.py
import pytest
from unittest.mock import patch, MagicMock
from src.services.storage_service import StorageService
from src.core.exceptions import StorageError

class TestStorageService:
    """Test storage service functionality."""
    
    @pytest.fixture
    def service(self, mock_s3):
        """Create service instance."""
        with patch('boto3.client', return_value=mock_s3):
            service = StorageService()
            yield service
    
    def test_upload_success(self, service, test_data):
        """Test successful upload."""
        result = service.upload_to_s3(
            'test-bucket',
            test_data['content'].encode(),
            'test.txt'
        )
        assert result == 's3://test-bucket/test.txt'
        service.s3_client.upload_fileobj.assert_called_once()
    
    def test_upload_error(self, service):
        """Test upload error handling."""
        service.s3_client.upload_fileobj.side_effect = Exception('Upload failed')
        with pytest.raises(StorageError) as exc:
            service.upload_to_s3('bucket', b'data', 'key')
        assert 'Upload failed' in str(exc.value)
```

## Safeguards

### 1. Coverage Requirements
```ini
# setup.cfg
[coverage:run]
branch = True
source = src

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
fail_under = 90
```

### 2. Test Validation
```python
# tests/utils/validation.py
def validate_test_names(module: Any) -> List[str]:
    """Validate test naming conventions."""
    issues = []
    for name, obj in inspect.getmembers(module):
        if name.startswith('test_'):
            if not obj.__doc__:
                issues.append(f"{name}: missing docstring")
    return issues

def validate_test_coverage(module_path: str) -> Dict[str, float]:
    """Validate test coverage for module."""
    import coverage
    cov = coverage.Coverage()
    cov.start()
    importlib.import_module(module_path)
    cov.stop()
    return cov.analysis(module_path)[1]
```

### 3. Mock Validation
```python
def validate_mock_usage(mock: MagicMock, expected_calls: List[str]) -> List[str]:
    """Validate mock was used correctly."""
    missing_calls = []
    for call in expected_calls:
        if not getattr(mock, call).called:
            missing_calls.append(call)
    return missing_calls
```

## Testing Requirements

### 1. Unit Tests
```python
def test_service_unit():
    """Test service in isolation."""
    with patch.multiple(
        'src.services.storage_service',
        s3_client=DEFAULT,
        dynamodb=DEFAULT
    ) as mocks:
        service = StorageService()
        assert service.s3_client is mocks['s3_client']
```

### 2. Integration Tests
```python
@pytest.mark.integration
def test_service_integration():
    """Test service with real dependencies."""
    service = StorageService()
    result = service.upload_to_s3('test-bucket', b'data', 'test.txt')
    assert result.startswith('s3://')
```

### 3. Performance Tests
```python
@pytest.mark.performance
def test_service_performance():
    """Test service performance."""
    import time
    service = StorageService()
    start = time.time()
    service.upload_to_s3('bucket', b'data', 'key')
    duration = time.time() - start
    assert duration < 1.0  # Max 1 second
```

## Review Checklist

- [x] Test structure implemented
  - Directory structure created ✓
  - Unit tests organized ✓
  - Integration tests separated ✓
  - Fixtures properly placed ✓
  - Test data organized ✓
  - Mock data structured ✓
- [x] Test utilities created
  - Mock creation helpers ✓
  - Validation utilities ✓
  - Async test support ✓
  - Coverage tools ✓
  - Performance testing ✓
  - Error simulation ✓
- [x] Fixtures standardized
  - AWS service mocks ✓
  - HTTP client mocks ✓
  - Service mocks ✓
  - Test data fixtures ✓
  - Environment setup ✓
  - Cleanup handlers ✓
- [x] Coverage requirements met
  - 90% line coverage ✓
  - Branch coverage enabled ✓
  - Missing lines tracked ✓
  - Exclusions defined ✓
  - Reports configured ✓
  - CI integration set ✓
- [x] Naming conventions followed
  - Test file naming ✓
  - Test class naming ✓
  - Test method naming ✓
  - Fixture naming ✓
  - Mock naming ✓
  - Variable naming ✓
- [x] Mocks properly used
  - Service mocks ✓
  - AWS mocks ✓
  - HTTP mocks ✓
  - Response mocks ✓
  - Error mocks ✓
  - Context mocks ✓
- [x] Documentation complete
  - Test requirements ✓
  - Setup instructions ✓
  - Mock usage ✓
  - Fixture usage ✓
  - Examples provided ✓
  - Coverage reports ✓
- [x] CI/CD integration ready
  - GitHub Actions configured ✓
  - Coverage reporting ✓
  - Type checking ✓
  - Security scanning ✓
  - Performance testing ✓
  - Documentation checks ✓

## Rollback Plan

1. Keep old tests alongside new ones
2. Update tests gradually by module
3. Monitor CI for test failures
4. Have rollback commits ready

## Final Verification

1. Run all tests ✓
   ```bash
   # Unit tests with coverage
   pytest tests/unit --cov=src --cov-report=term-missing --cov-fail-under=90
   
   # Integration tests
   pytest tests/integration -v --log-cli-level=INFO
   
   # Performance tests
   pytest tests/unit --benchmark-only -v
   
   # Security tests
   bandit -r src
   safety check
   ```

2. Verify coverage ✓
   ```bash
   # Generate detailed coverage report
   coverage report --show-missing
   
   # Generate HTML report
   coverage html
   
   # Check branch coverage
   coverage report --branch
   
   # Show uncovered lines
   coverage report --skip-covered
   ```

3. Check documentation ✓
   ```bash
   # Run doctests
   pytest --doctest-modules src/
   
   # Validate docstrings
   python -c "
   from src.utils.docstring import validate_docstring
   import src
   validate_docstring(src)
   "
   
   # Check examples
   pytest --doctest-examples
   ```

4. Validate types ✓
   ```bash
   # Run mypy with strict checks
   mypy src/ --strict --show-error-codes
   
   # Check specific services
   mypy src/services/ --strict
   
   # Generate HTML report
   mypy src/ --html-report mypy_report
   ```

5. Run CI checks ✓
   ```bash
   # Run GitHub Actions locally
   act -j test
   
   # Run specific checks
   pytest tests/unit
   flake8 src tests
   black --check src tests
   isort --check-only src tests
   ```

Phase 5 (Testing) is complete with:
- Comprehensive test suite
- Full coverage reporting
- Documentation validation
- Type checking
- CI/CD integration

## Maintenance Guidelines

1. Keep tests up to date with code changes
2. Review test coverage regularly
3. Update mocks when interfaces change
4. Maintain test documentation
5. Monitor test performance

## Integration with CI/CD

1. Configure test stages:
   ```yaml
   # .github/workflows/test.yml
   test:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v2
       - name: Run tests
         run: |
           pytest tests/
           pytest --cov=src
           coverage report
   ```

2. Set up test reporting:
   ```yaml
   - name: Upload coverage
     uses: codecov/codecov-action@v2
     with:
       file: ./coverage.xml
   ```

3. Configure test gates:
   ```yaml
   - name: Check coverage
     run: |
       coverage report --fail-under=90