# Office Assistant - Configuration Management Guide

## Overview

This guide documents the comprehensive configuration management system for the Office Assistant application. The system provides a schema-driven approach to managing 96+ configurable parameters across 12 major categories.

## 📁 Files Created

### 1. **admin_config_schema.json**
- Complete JSON schema defining all configurable parameters
- Includes validation rules, UI metadata, and dependencies
- Contains 12 configuration sections with 96+ fields
- Supports multiple field types (text, secret, number, boolean, select, etc.)

### 2. **config_manager.py**
- Python configuration management class
- Loads and validates configuration against schema
- Supports environment variables and .env files
- Provides validation, import/export, and type conversion
- Includes connection testing framework

### 3. **.env.example**
- Template environment file with all configurable parameters
- Includes descriptions, defaults, and documentation links
- Security warnings for sensitive fields
- Ready to copy and customize

### 4. **admin_ui_example.md**
- Complete implementation guide for building admin UI
- React/TypeScript component examples
- FastAPI backend API examples
- Security best practices and deployment guide

## 📊 Configuration Categories

### 1. **Security & Authentication** (14 parameters)
Critical API keys and credentials:
- OpenAI, Gemini, Cerebras, OpenRouter API keys
- Google services (Calendar, Custom Search, API)
- Weaviate, OpenWeather API keys
- Slack and Telegram bot tokens
- ERPNext and Odoo credentials

**🔴 CRITICAL SECURITY ISSUES FOUND:**
- Hardcoded Odoo password in `config.py:32` and `odoo_functions.py:12`
- Proxy credentials exposed in `config.py:38`

### 2. **ERP Integrations** (7 parameters)
- ERPNext: Base URL, API key, API secret
- Odoo: URL, database name, username, password

### 3. **Database & Storage** (9 parameters)
- Weaviate: URL, collections, connection pools
- DynamoDB: Tables for users, channels, meetings, URLs
- S3: Image and document buckets

### 4. **AI Model Configuration** (14 parameters)
- Model selection (GPT-5, Gemini, Cerebras, Whisper, TTS)
- Temperature and token limits
- Reasoning parameters (verbosity, reasoning effort)
- Sampling parameters (top-K, top-P)

### 5. **Performance & Timeouts** (11 parameters)
- HTTP timeouts (default: 30s, GPT-5: 120s, Gemini: 300s)
- Retry logic (Cerebras: 3 attempts, Telegram: 3 attempts)
- Connection pool timeouts
- Task execution timeouts

### 6. **Rate Limits & Concurrency** (11 parameters)
- Concurrent request limits (5 max, 2 per host)
- Connection pool sizes (Weaviate: 5+2, Generic: 5+2)
- Message and file size limits
- Content download limits

### 7. **Network & Proxy** (2 parameters)
- HTTP proxy URL configuration
- User agent rotation toggle

### 8. **Media & Audio** (1 parameter)
- Audio sample rate (44.1 kHz default)

### 9. **Web Scraping** (3 parameters)
- Allowed content types whitelist
- Blocked file extensions
- URL pattern blocking toggle

### 10. **Excel Export Styling** (3 parameters)
- Color scheme selection (8 options)
- Header row height
- Column width cap

### 11. **Feature Flags** (10 parameters)
Enable/disable integrations:
- Odoo, ERPNext, Slack, Telegram
- Message router, semantic routing
- Web scraping, weather service
- Google Calendar, URL shortener

### 12. **Advanced Configuration** (4 parameters)
- NLTK data path
- Routes layer configuration file
- Logging level
- Debug mode

## 🚀 Quick Start

### Step 1: Set Up Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env  # or use your preferred editor
```

### Step 2: Use the Configuration Manager

```python
from config_manager import get_config_manager, get_config, is_feature_enabled

# Get the configuration manager
config = get_config_manager()

# Get a configuration value
openai_key = config.get('openai_api_key')
temperature = config.get('ai_temperature', default=1.0)

# Or use convenience functions
api_key = get_config('openai_api_key')

# Check feature flags
if is_feature_enabled('enable_slack_integration'):
    # Initialize Slack integration
    pass

# Set a configuration value
config.set('ai_temperature', 0.7, persist=True)

# Validate all configuration
validation = config.validate_all()
if validation:
    print("Configuration errors found:")
    for field_id, error_info in validation.items():
        print(f"  {error_info['field']}: {error_info['errors']}")

# Get missing required fields
missing = config.get_missing_required()
if missing:
    print("Missing required configuration:")
    for item in missing:
        print(f"  - {item['label']} ({item['env_var']})")

# Export to .env file
env_content = config.export_to_env('config_backup.env')

# Import from .env file
result = config.import_from_env('new_config.env')
print(f"Imported {result['imported']} fields")
```

### Step 3: Migrate Existing Code

Replace hardcoded values with configuration manager:

**Before:**
```python
# config.py
odoo_password = "Carbon123#"  # HARDCODED!
ai_temperature = 1
```

**After:**
```python
# config.py
from config_manager import get_config

# These will come from environment variables
odoo_password = get_config('odoo_password')
ai_temperature = get_config('ai_temperature', default=1)
```

## 🔒 Security Best Practices

### Immediate Actions Required

1. **Fix Hardcoded Credentials**
   ```bash
   # Set environment variable instead
   export ODOO_PASSWORD="your_secure_password"
   export HTTP_PROXY_URL="http://user:pass@proxy:port"
   ```

2. **Update config.py and odoo_functions.py**
   ```python
   # Replace hardcoded values with:
   from config_manager import get_config

   odoo_password = get_config('odoo_password')
   proxy_url = get_config('proxy_url')
   ```

3. **Ensure .env is in .gitignore**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo ".env.local" >> .gitignore
   ```

### Ongoing Security

- ✅ Never commit .env files to version control
- ✅ Rotate API keys regularly
- ✅ Use least-privilege access for service accounts
- ✅ Enable audit logging for configuration changes
- ✅ Use secrets management services in production (AWS Secrets Manager, HashiCorp Vault)
- ✅ Encrypt secrets at rest
- ✅ Use HTTPS for all API communications

## 🎨 Admin UI Implementation

### Option 1: React + Material-UI (Recommended)

See [admin_ui_example.md](admin_ui_example.md) for complete implementation.

**Key Features:**
- Tab-based navigation by section
- Field-specific components (text, secret, number, boolean, select)
- Real-time validation with error messages
- Test connection buttons for API keys
- Import/export .env functionality
- Change tracking and modified indicators
- Search and filter capabilities

### Option 2: FastAPI Backend API

Complete REST API for configuration management:

```bash
# Install dependencies
pip install fastapi uvicorn python-dotenv

# Run the API server
python config_api.py
# or
uvicorn config_api:app --reload

# Access API docs
# http://localhost:8000/docs
```

**API Endpoints:**
- `GET /api/config/` - Get all configuration
- `POST /api/config/` - Update configuration
- `GET /api/config/validate/missing` - Get missing required fields
- `POST /api/config/validate` - Validate configuration
- `POST /api/config/test/{field_id}` - Test connection
- `GET /api/config/export` - Export as .env
- `POST /api/config/import` - Import from .env
- `GET /api/config/features` - Get feature flags

## 📈 Usage Examples

### Example 1: Check Configuration Status

```python
from config_manager import get_config_manager

config = get_config_manager()

# Get all missing required fields
missing = config.get_missing_required()

if missing:
    print("⚠️  Configuration incomplete!")
    print(f"Missing {len(missing)} required fields:\n")

    for item in missing:
        print(f"❌ {item['label']}")
        print(f"   Environment Variable: {item['env_var']}")
        print(f"   Section: {item['section']}")
        print(f"   Errors: {', '.join(item['errors'])}")
        print()
else:
    print("✅ All required configuration fields are set!")
```

### Example 2: Export Configuration Backup

```python
from config_manager import get_config_manager
from datetime import datetime

config = get_config_manager()

# Create timestamped backup
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f'config_backup_{timestamp}.env'

config.export_to_env(backup_file, include_comments=True)
print(f"✅ Configuration backed up to {backup_file}")
```

### Example 3: Validate Before Deployment

```python
from config_manager import get_config_manager
import sys

config = get_config_manager()

# Validate all configuration
errors = config.validate_all()

if errors:
    print("❌ Configuration validation failed!")
    for field_id, error_info in errors.items():
        print(f"\n{error_info['field']} ({error_info['section']}):")
        for error in error_info['errors']:
            print(f"  - {error}")
    sys.exit(1)
else:
    print("✅ Configuration validation passed!")
    sys.exit(0)
```

### Example 4: Feature Flag Usage

```python
from config_manager import is_feature_enabled

# Check if features are enabled before initializing
if is_feature_enabled('enable_slack_integration'):
    from slack_integration import initialize_slack
    initialize_slack()

if is_feature_enabled('enable_telegram_integration'):
    from telegram_integration import initialize_telegram
    initialize_telegram()

if is_feature_enabled('enable_odoo_integration'):
    from odoo_functions import initialize_odoo
    initialize_odoo()
```

### Example 5: Dynamic Configuration Updates

```python
from config_manager import get_config_manager

config = get_config_manager()

# Update configuration programmatically
config.set('ai_temperature', 0.5, persist=True)
config.set('max_tokens', 8000, persist=True)

# Verify the changes
print(f"Temperature: {config.get('ai_temperature')}")
print(f"Max Tokens: {config.get('max_tokens')}")
```

## 🔧 Migration Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Fill in all required API keys and credentials
- [ ] Remove hardcoded credentials from source code
  - [ ] `config.py:32` - odoo_password
  - [ ] `config.py:38` - proxy_url
  - [ ] `odoo_functions.py:12` - odoo_password
- [ ] Replace hardcoded values with `get_config()` calls
- [ ] Add `.env` to `.gitignore`
- [ ] Run validation: `python config_manager.py`
- [ ] Test all integrations
- [ ] Deploy admin UI (optional)
- [ ] Set up configuration backup process
- [ ] Document custom configuration for team

## 📝 Schema Customization

To add new configuration parameters:

1. **Update admin_config_schema.json**
   ```json
   {
     "id": "my_new_field",
     "label": "My New Field",
     "type": "text",
     "required": false,
     "env_var": "MY_NEW_FIELD",
     "default": "default_value",
     "description": "Description of the field",
     "validation": {
       "pattern": "^[A-Za-z]+$",
       "errorMessage": "Must contain only letters"
     }
   }
   ```

2. **Update .env.example**
   ```bash
   # My New Field
   # Description of the field
   MY_NEW_FIELD=default_value
   ```

3. **Use in code**
   ```python
   from config_manager import get_config

   my_value = get_config('my_new_field')
   ```

## 🧪 Testing

```python
# Run the configuration manager test
python config_manager.py

# Output:
# === Configuration Manager Test ===
#
# Available sections:
#   - Security & Authentication (security)
#   - ERP Integrations (erp_integrations)
#   ...
#
# === Missing Required Fields ===
#   - OpenAI API Key (OPENAI_API_KEY)
#     Error: OpenAI API Key is required
#   ...
#
# === Feature Flags ===
#   enable_odoo_integration: ✓ Enabled
#   enable_slack_integration: ✓ Enabled
#   ...
```

## 📚 Additional Resources

- [admin_config_schema.json](admin_config_schema.json) - Complete schema definition
- [config_manager.py](config_manager.py) - Configuration manager implementation
- [.env.example](.env.example) - Environment variable template
- [admin_ui_example.md](admin_ui_example.md) - UI implementation guide

## 🤝 Support

For questions or issues:
1. Check this guide first
2. Review the schema documentation in `admin_config_schema.json`
3. Examine example code in `config_manager.py`
4. Consult the UI implementation guide in `admin_ui_example.md`

## 📄 License

This configuration system is part of the Office Assistant application.

---

**Last Updated:** 2025-11-25
**Schema Version:** 1.0.0
