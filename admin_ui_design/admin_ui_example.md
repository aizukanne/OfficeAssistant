# Admin Configuration UI - Implementation Guide

This document provides implementation examples for building the admin configuration UI based on the `admin_config_schema.json`.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Admin UI Frontend                      │
│  (React/Vue/Angular + Tailwind/Material-UI/Ant Design)  │
├─────────────────────────────────────────────────────────┤
│                    REST API Layer                        │
│              (FastAPI/Flask/Express)                     │
├─────────────────────────────────────────────────────────┤
│              ConfigurationManager (Python)               │
├─────────────────────────────────────────────────────────┤
│         admin_config_schema.json (Schema)                │
├─────────────────────────────────────────────────────────┤
│              .env file (Persistence)                     │
└─────────────────────────────────────────────────────────┘
```

## 1. React Component Structure (Recommended)

### Directory Structure

```
admin-ui/
├── src/
│   ├── components/
│   │   ├── ConfigurationPanel.tsx       # Main container
│   │   ├── ConfigurationSection.tsx     # Section wrapper
│   │   ├── ConfigurationField.tsx       # Individual field
│   │   ├── fields/
│   │   │   ├── TextField.tsx
│   │   │   ├── SecretField.tsx
│   │   │   ├── SelectField.tsx
│   │   │   ├── NumberField.tsx
│   │   │   ├── BooleanField.tsx
│   │   │   ├── MultiSelectField.tsx
│   │   │   ├── TagsField.tsx
│   │   │   └── UrlField.tsx
│   │   ├── TestConnectionButton.tsx
│   │   └── ValidationMessage.tsx
│   ├── hooks/
│   │   ├── useConfiguration.ts
│   │   ├── useValidation.ts
│   │   └── useTestConnection.ts
│   ├── services/
│   │   └── configApi.ts
│   ├── types/
│   │   └── config.types.ts
│   └── utils/
│       └── validators.ts
└── admin_config_schema.json
```

### Example Component: ConfigurationPanel.tsx

```typescript
import React, { useState, useEffect } from 'react';
import { Tabs, Tab, Button, Alert, Snackbar } from '@mui/material';
import { Save, Refresh, FileDownload, FileUpload } from '@mui/icons-material';
import ConfigurationSection from './ConfigurationSection';
import { useConfiguration } from '../hooks/useConfiguration';
import schema from '../admin_config_schema.json';

interface ConfigurationPanelProps {
  onSave?: (config: any) => void;
}

const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({ onSave }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [showSuccess, setShowSuccess] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  const {
    config,
    loading,
    saveConfig,
    resetConfig,
    exportConfig,
    importConfig,
    testConnection,
    validateAll
  } = useConfiguration();

  const sections = schema.sections.sort((a, b) => a.priority - b.priority);

  const handleSave = async () => {
    const validation = await validateAll();

    if (validation.valid) {
      await saveConfig();
      setShowSuccess(true);
      onSave?.(config);
    } else {
      setErrors(validation.errors);
    }
  };

  const handleExport = () => {
    const envContent = exportConfig();
    const blob = new Blob([envContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '.env';
    a.click();
  };

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const content = e.target?.result as string;
        await importConfig(content);
      };
      reader.readAsText(file);
    }
  };

  return (
    <div className="configuration-panel">
      <div className="header">
        <h1>Office Assistant Configuration</h1>
        <div className="actions">
          <Button
            startIcon={<FileDownload />}
            onClick={handleExport}
            variant="outlined"
          >
            Export .env
          </Button>
          <Button
            startIcon={<FileUpload />}
            component="label"
            variant="outlined"
          >
            Import .env
            <input
              type="file"
              hidden
              accept=".env"
              onChange={handleImport}
            />
          </Button>
          <Button
            startIcon={<Refresh />}
            onClick={resetConfig}
            variant="outlined"
            color="warning"
          >
            Reset to Defaults
          </Button>
          <Button
            startIcon={<Save />}
            onClick={handleSave}
            variant="contained"
            color="primary"
          >
            Save Configuration
          </Button>
        </div>
      </div>

      {errors.length > 0 && (
        <Alert severity="error" onClose={() => setErrors([])}>
          <strong>Validation Errors:</strong>
          <ul>
            {errors.map((error, idx) => (
              <li key={idx}>{error}</li>
            ))}
          </ul>
        </Alert>
      )}

      <Tabs
        value={activeTab}
        onChange={(_, newValue) => setActiveTab(newValue)}
        variant="scrollable"
        scrollButtons="auto"
      >
        {sections.map((section) => (
          <Tab
            key={section.id}
            label={section.title}
            icon={getIcon(section.icon)}
          />
        ))}
      </Tabs>

      {sections.map((section, idx) => (
        <div
          key={section.id}
          role="tabpanel"
          hidden={activeTab !== idx}
        >
          {activeTab === idx && (
            <ConfigurationSection
              section={section}
              config={config}
              onTestConnection={testConnection}
            />
          )}
        </div>
      ))}

      <Snackbar
        open={showSuccess}
        autoHideDuration={3000}
        onClose={() => setShowSuccess(false)}
        message="Configuration saved successfully"
      />
    </div>
  );
};

export default ConfigurationPanel;
```

### Example Component: SecretField.tsx

```typescript
import React, { useState } from 'react';
import {
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
  Chip
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Warning,
  CheckCircle
} from '@mui/icons-material';

interface SecretFieldProps {
  field: any;
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  error?: string;
  testEndpoint?: string;
  onTest?: () => void;
}

const SecretField: React.FC<SecretFieldProps> = ({
  field,
  value,
  onChange,
  onBlur,
  error,
  testEndpoint,
  onTest
}) => {
  const [showSecret, setShowSecret] = useState(false);
  const [isTested, setIsTested] = useState(false);

  const maskedValue = value
    ? `${'•'.repeat(Math.max(0, value.length - 4))}${value.slice(-4)}`
    : '';

  const handleTest = async () => {
    if (onTest) {
      await onTest();
      setIsTested(true);
    }
  };

  return (
    <div className="secret-field">
      <TextField
        fullWidth
        type={showSecret ? 'text' : 'password'}
        label={field.label}
        value={showSecret ? value : maskedValue}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        error={!!error}
        helperText={error || field.description}
        required={field.required}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <IconButton
                onClick={() => setShowSecret(!showSecret)}
                edge="end"
              >
                {showSecret ? <VisibilityOff /> : <Visibility />}
              </IconButton>
            </InputAdornment>
          )
        }}
      />

      <div className="field-metadata">
        {field.security_warning && (
          <Chip
            icon={<Warning />}
            label={field.security_warning}
            color="warning"
            size="small"
          />
        )}

        {testEndpoint && (
          <Chip
            icon={isTested ? <CheckCircle /> : undefined}
            label="Test Connection"
            color={isTested ? 'success' : 'default'}
            onClick={handleTest}
            clickable
            size="small"
          />
        )}

        {field.documentation_url && (
          <a
            href={field.documentation_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            Documentation
          </a>
        )}
      </div>

      <div className="env-var-name">
        <code>{field.env_var}</code>
      </div>
    </div>
  );
};

export default SecretField;
```

### Example Hook: useConfiguration.ts

```typescript
import { useState, useEffect, useCallback } from 'react';
import { configApi } from '../services/configApi';

export const useConfiguration = () => {
  const [config, setConfig] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const data = await configApi.getAll();
      setConfig(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    try {
      await configApi.save(config);
    } catch (err) {
      throw new Error(`Failed to save configuration: ${err.message}`);
    }
  };

  const updateField = useCallback((fieldId: string, value: any) => {
    setConfig((prev: any) => ({
      ...prev,
      [fieldId]: value
    }));
  }, []);

  const resetConfig = async () => {
    try {
      const defaults = await configApi.getDefaults();
      setConfig(defaults);
    } catch (err) {
      setError(err.message);
    }
  };

  const validateAll = async () => {
    try {
      return await configApi.validateAll(config);
    } catch (err) {
      return { valid: false, errors: [err.message] };
    }
  };

  const testConnection = async (fieldId: string) => {
    try {
      return await configApi.testConnection(fieldId, config[fieldId]);
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const exportConfig = () => {
    return configApi.exportToEnv(config);
  };

  const importConfig = async (envContent: string) => {
    try {
      const imported = await configApi.importFromEnv(envContent);
      setConfig(imported);
    } catch (err) {
      setError(err.message);
    }
  };

  return {
    config,
    loading,
    error,
    updateField,
    saveConfig,
    resetConfig,
    validateAll,
    testConnection,
    exportConfig,
    importConfig
  };
};
```

### Example API Service: configApi.ts

```typescript
const API_BASE_URL = '/api/config';

export const configApi = {
  async getAll() {
    const response = await fetch(`${API_BASE_URL}/`);
    if (!response.ok) throw new Error('Failed to fetch configuration');
    return response.json();
  },

  async save(config: any) {
    const response = await fetch(`${API_BASE_URL}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (!response.ok) throw new Error('Failed to save configuration');
    return response.json();
  },

  async getDefaults() {
    const response = await fetch(`${API_BASE_URL}/defaults`);
    if (!response.ok) throw new Error('Failed to fetch defaults');
    return response.json();
  },

  async validateAll(config: any) {
    const response = await fetch(`${API_BASE_URL}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (!response.ok) throw new Error('Validation failed');
    return response.json();
  },

  async testConnection(fieldId: string, value: any) {
    const response = await fetch(`${API_BASE_URL}/test/${fieldId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value })
    });
    if (!response.ok) throw new Error('Connection test failed');
    return response.json();
  },

  exportToEnv(config: any): string {
    // Convert config object to .env format
    return Object.entries(config)
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');
  },

  async importFromEnv(envContent: string) {
    const response = await fetch(`${API_BASE_URL}/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: envContent
    });
    if (!response.ok) throw new Error('Import failed');
    return response.json();
  }
};
```

## 2. Backend API (FastAPI)

### Example FastAPI Server: config_api.py

```python
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from config_manager import get_config_manager

app = FastAPI(title="Office Assistant Configuration API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config_manager = get_config_manager()


class ConfigUpdate(BaseModel):
    field_id: str
    value: Any


class BulkConfigUpdate(BaseModel):
    config: Dict[str, Any]


@app.get("/api/config/")
async def get_all_config():
    """Get all configuration values."""
    all_fields = config_manager.get_all_fields()
    config = {}

    for field in all_fields:
        field_id = field['id']
        config[field_id] = {
            'value': config_manager.get(field_id),
            'field': field
        }

    return config


@app.get("/api/config/{field_id}")
async def get_config_field(field_id: str):
    """Get a specific configuration field value."""
    field = config_manager.get_field(field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    return {
        'value': config_manager.get(field_id),
        'field': field
    }


@app.post("/api/config/{field_id}")
async def update_config_field(field_id: str, update: ConfigUpdate):
    """Update a specific configuration field."""
    try:
        config_manager.set(update.field_id, update.value, persist=True)
        return {"success": True, "field_id": field_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/config/")
async def update_bulk_config(update: BulkConfigUpdate):
    """Update multiple configuration fields at once."""
    errors = []
    updated = []

    for field_id, value in update.config.items():
        try:
            config_manager.set(field_id, value, persist=True)
            updated.append(field_id)
        except ValueError as e:
            errors.append({"field_id": field_id, "error": str(e)})

    return {
        "success": len(errors) == 0,
        "updated": updated,
        "errors": errors
    }


@app.get("/api/config/defaults")
async def get_defaults():
    """Get default values for all configuration fields."""
    all_fields = config_manager.get_all_fields()
    defaults = {}

    for field in all_fields:
        if 'default' in field:
            defaults[field['id']] = field['default']

    return defaults


@app.post("/api/config/validate")
async def validate_config(config: Dict[str, Any] = Body(...)):
    """Validate configuration values."""
    errors = []

    for field_id, value in config.items():
        validation = config_manager.validate_field(field_id, value)
        if not validation['valid']:
            errors.append({
                'field_id': field_id,
                'errors': validation['errors']
            })

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


@app.get("/api/config/validate/missing")
async def get_missing_required():
    """Get all missing required configuration fields."""
    missing = config_manager.get_missing_required()
    return {
        'missing': missing,
        'count': len(missing)
    }


@app.post("/api/config/test/{field_id}")
async def test_connection(field_id: str, body: Dict[str, Any] = Body(...)):
    """Test a connection for a specific field."""
    value = body.get('value')
    result = config_manager.test_connection(field_id)
    return result


@app.get("/api/config/export")
async def export_config(include_comments: bool = True):
    """Export configuration as .env file content."""
    content = config_manager.export_to_env(include_comments=include_comments)
    return {"content": content}


@app.post("/api/config/import")
async def import_config(env_content: str = Body(..., media_type="text/plain")):
    """Import configuration from .env file content."""
    # Write to temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(env_content)
        temp_path = f.name

    try:
        result = config_manager.import_from_env(temp_path)
        return result
    finally:
        import os
        os.unlink(temp_path)


@app.get("/api/config/sections")
async def get_sections():
    """Get all configuration sections."""
    return config_manager.schema.get('sections', [])


@app.get("/api/config/sections/{section_id}")
async def get_section_config(section_id: str):
    """Get configuration for a specific section."""
    section = config_manager.get_section(section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    config = config_manager.get_section_config(section_id)
    return {
        'section': section,
        'config': config
    }


@app.get("/api/config/features")
async def get_feature_flags():
    """Get all feature flag settings."""
    return config_manager.get_feature_flags()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 3. UI Components Library Recommendations

### Option A: Material-UI (MUI)
- Best for: Enterprise applications, comprehensive component library
- Components: TextField, Select, Switch, Slider, Tabs
- Styling: Emotion/styled-components

### Option B: Ant Design
- Best for: Admin panels, data-heavy applications
- Components: Form, Input, Select, Switch, Tabs, Table
- Built-in form validation

### Option C: Tailwind CSS + Headless UI
- Best for: Custom designs, flexibility
- Lightweight, utility-first approach
- Full control over styling

## 4. Security Considerations

### Frontend
- Mask secret fields by default
- Require confirmation to view secrets
- Never log secret values
- Use HTTPS for all API calls
- Implement CSRF protection

### Backend
- Encrypt secrets at rest
- Use environment variables, never hardcode
- Implement role-based access control (RBAC)
- Audit all configuration changes
- Rate limit API endpoints

### Storage
- Store .env files outside web root
- Set appropriate file permissions (600)
- Use secrets management services (AWS Secrets Manager, HashiCorp Vault)
- Backup configuration before changes

## 5. Additional Features

### Search and Filter
```typescript
const [searchTerm, setSearchTerm] = useState('');

const filteredSections = sections.map(section => ({
  ...section,
  fields: section.fields.filter(field =>
    field.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
    field.description.toLowerCase().includes(searchTerm.toLowerCase())
  )
})).filter(section => section.fields.length > 0);
```

### Change Tracking
```typescript
const [modifiedFields, setModifiedFields] = useState<Set<string>>(new Set());

const handleFieldChange = (fieldId: string, value: any) => {
  updateField(fieldId, value);
  setModifiedFields(prev => new Set(prev).add(fieldId));
};
```

### Bulk Operations
```typescript
const handleResetSection = (sectionId: string) => {
  const section = getSection(sectionId);
  section.fields.forEach(field => {
    if (field.default !== undefined) {
      updateField(field.id, field.default);
    }
  });
};
```

## 6. Testing Strategy

### Unit Tests
- Test individual field components
- Test validation logic
- Test API service functions

### Integration Tests
- Test form submission
- Test import/export functionality
- Test connection testing

### E2E Tests
- Test complete configuration workflow
- Test error handling
- Test security features

## Deployment

### Docker Setup
```dockerfile
# Frontend
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]

# Backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "config_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
```bash
# Production
NODE_ENV=production
API_URL=https://api.yourapp.com
ENABLE_ANALYTICS=true

# Development
NODE_ENV=development
API_URL=http://localhost:8000
ENABLE_ANALYTICS=false
```
