# Odoo and ERPNext Removal Recommendations

## Current Issues
1. Removed Odoo configuration but ERPNext imports remain
2. Lambda function includes both Odoo and ERPNext functions
3. ERPNext API keys still referenced
4. Mixed usage of Odoo/ERPNext terminology

## Required Changes

### 1. Remove Configuration
From settings.py:
```python
# Remove these variables
ERPNEXT_API_KEY = os.getenv('ERPNEXT_API_KEY')
ERPNEXT_API_SECRET = os.getenv('ERPNEXT_API_SECRET')
ODOO_URL = os.getenv('ODOO_URL')
ODOO_DB = os.getenv('ODOO_DB')
ODOO_LOGIN = os.getenv('ODOO_USERNAME')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD')

# Remove these configurations
ODOO_CONFIG = {
    'url': ODOO_URL,
    'db': ODOO_DB,
    'username': ODOO_LOGIN,
    'password': ODOO_PASSWORD
}
```

### 2. Clean Lambda Function
Remove all ERP-related imports and functions:
```python
# Remove these imports
from src.services import (
    get_models,          # ERPNext/Odoo
    get_fields,          # ERPNext/Odoo
    create_record,       # ERPNext/Odoo
    fetch_records,       # ERPNext/Odoo
    update_record,       # ERPNext/Odoo
    delete_records,      # ERPNext/Odoo
    print_record         # ERPNext/Odoo
)

# Remove from available_functions
available_functions = {
    # ... other functions ...
    "get_models": get_models,            # Remove
    "get_fields": get_fields,            # Remove
    "create_record": create_record,      # Remove
    "fetch_records": fetch_records,      # Remove
    "update_record": update_record,      # Remove
    "delete_records": delete_records,    # Remove
    "print_record": print_record         # Remove
}
```

### 3. Remove Service Modules
```bash
# Remove Odoo service
rm -rf src/services/odoo/

# Remove any ERPNext-specific files
find src/ -type f -exec grep -l "erpnext" {} \; | xargs rm -f
```

### 4. Clean Service Exports
Update src/services/__init__.py:
- Remove Odoo service exports
- Remove ERPNext function exports
- Remove any related type hints

### 5. Update Documentation
- Remove Odoo documentation
- Remove ERPNext documentation
- Update API documentation
- Update configuration guides

## Implementation Steps

1. Remove Configuration:
- Remove all ERP-related environment variables
- Remove configuration sections
- Update validation logic

2. Clean Code:
- Remove service modules
- Clean up imports
- Remove functions
- Update type hints

3. Update Documentation:
- Remove ERP sections
- Update API docs
- Update configuration guides
- Update deployment guides

## Verification Steps

1. Check No References:
```bash
# Check for any remaining references
grep -r "odoo" .
grep -r "erpnext" .
```

2. Verify Imports:
- No ERP-related imports remain
- No ERP functions referenced
- No ERP configuration used

3. Test Functionality:
- Lambda function works without ERP
- No ERP-related errors
- All other services functional

## Migration Notes

### For Development Team
1. Remove Code:
   - Delete ERP service modules
   - Clean up imports
   - Remove ERP functions

2. Update Tests:
   - Remove ERP-related tests
   - Update integration tests
   - Verify remaining functionality

### For Operations Team
1. Update Environment:
   - Remove ERP variables
   - Update deployment scripts
   - Update monitoring

2. Documentation:
   - Update API docs
   - Update configuration guides
   - Update deployment guides

## Rollback Plan
1. Keep backup of:
   - ERP service code
   - Configuration files
   - Documentation

2. Monitor for:
   - Integration issues
   - Missing functionality
   - Unexpected dependencies

3. Have ready:
   - Original code
   - Configuration backups
   - Deployment scripts