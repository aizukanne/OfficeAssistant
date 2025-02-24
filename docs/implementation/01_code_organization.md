# Phase 1: Code Organization Implementation

## Objective
Reorganize the codebase to follow proper separation of concerns and establish clear module boundaries.

## Current Issues
1. Services in flat structure
2. Functions in __init__.py
3. Mixed concerns in service files
4. Unclear module boundaries

## Implementation Steps

### 1. Create New Directory Structure
```
src/
  ├── services/
  │   ├── __init__.py           # Only imports/exports
  │   ├── storage/
  │   │   ├── __init__.py       # Public interface
  │   │   ├── service.py        # Service implementation
  │   │   ├── functions.py      # Public functions
  │   │   └── constants.py      # Constants and configs
  │   ├── slack/
  │   │   ├── __init__.py
  │   │   └── service.py
  │   ├── openai/
  │   │   ├── __init__.py
  │   │   └── service.py
  │   └── odoo/
  │       ├── __init__.py
  │       └── service.py
  └── interfaces/
      └── __init__.py           # All interfaces
```

### 2. Move Service Implementations
1. Create new directories for each service
2. Move service classes to service.py files
3. Move public functions to functions.py files
4. Update imports to reflect new structure

Example:
```python
# src/services/storage/service.py
from src.interfaces import StorageServiceInterface

class StorageService(StorageServiceInterface):
    """Storage service implementation."""
    pass

# src/services/storage/functions.py
from .service import get_instance

def upload_to_s3(bucket: str, file_data: bytes, ...) -> str:
    """Upload file to S3."""
    return get_instance().upload_to_s3(...)
```

### 3. Clean Up __init__.py Files
1. Remove all function implementations
2. Only include imports and exports
3. Maintain backward compatibility

Example:
```python
# src/services/__init__.py
from .storage import StorageService, upload_to_s3, download_from_s3
from .slack import SlackService

__all__ = [
    'StorageService',
    'upload_to_s3',
    'download_from_s3',
    'SlackService'
]
```

### 4. Update Interface Locations
1. Move all interfaces to src/interfaces
2. Update imports in service files
3. Maintain interface consistency

## Safeguards

### 1. Backward Compatibility
- Keep existing function signatures unchanged
- Maintain current import paths
- Add deprecation warnings for old patterns

### 2. Import Protection
```python
# src/services/storage/__init__.py
from .service import StorageService
from .functions import upload_to_s3

# Prevent direct import of implementation details
__all__ = ['StorageService', 'upload_to_s3']
```

### 3. Version Control
```python
# src/services/storage/service.py
__version__ = '1.0.0'

def get_version() -> str:
    """Get service version."""
    return __version__
```

## Testing Requirements

### 1. Directory Structure Tests
```python
def test_service_structure():
    """Verify service directory structure."""
    assert os.path.exists('src/services/storage/service.py')
    assert os.path.exists('src/services/storage/functions.py')
```

### 2. Import Tests
```python
def test_public_imports():
    """Verify public imports work."""
    from src.services import StorageService, upload_to_s3
    assert StorageService is not None
    assert upload_to_s3 is not None
```

### 3. Backward Compatibility Tests
```python
def test_backward_compatibility():
    """Verify old imports still work."""
    from src.services import upload_to_s3
    result = upload_to_s3('bucket', b'data', 'key')
    assert result is not None
```

## Review Checklist

- [x] All services moved to dedicated directories
  - storage/ ✓
  - slack/ ✓
  - openai/ ✓
  - odoo/ ✓
  - external/ ✓
- [x] __init__.py files only contain imports/exports
  - Main services/__init__.py cleaned ✓
  - Each service's __init__.py properly structured ✓
- [x] All interfaces moved to src/interfaces
  - ServiceInterface ✓
  - StorageServiceInterface ✓
  - MessageServiceInterface ✓
  - AIServiceInterface ✓
  - ExternalServiceInterface ✓
- [x] Imports updated throughout codebase
  - All services using proper imports ✓
  - No circular dependencies ✓
  - Clear module boundaries ✓
- [ ] Tests passing (to be verified in next phase)
- [x] No direct implementation imports
  - All services using public interfaces ✓
  - Implementation details properly hidden ✓
- [x] Backward compatibility maintained
  - Function signatures unchanged ✓
  - Import paths maintained ✓
  - Public API preserved ✓
- [x] Documentation updated
  - Service docstrings complete ✓
  - Interface documentation updated ✓
  - Examples provided ✓

## Rollback Plan

1. Keep old file structure until all tests pass
2. Maintain backup of original files
3. Deploy changes gradually
4. Monitor for import errors
5. Have quick rollback script ready

## Next Phase Preparation

1. Document new file locations
2. Update import patterns
3. Note any technical debt
4. Identify potential logging impacts
5. List affected tests

## Dependencies for Next Phase

The logging phase will need to:
1. Update logger imports in new locations
2. Maintain consistent service names
3. Respect new module boundaries
4. Update tests to match new structure