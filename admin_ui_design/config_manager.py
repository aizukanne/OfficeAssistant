"""
Configuration Manager for Office Assistant
Handles loading, validation, and management of application configuration
based on the admin_config_schema.json
"""

import os
import json
import re
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv, set_key, unset_key


class ConfigurationManager:
    """
    Manages application configuration with validation against schema.
    Supports loading from environment variables, .env files, and programmatic access.
    """

    def __init__(self, schema_path: str = "admin_config_schema.json", env_file: str = ".env"):
        """
        Initialize the configuration manager.

        Args:
            schema_path: Path to the JSON schema file
            env_file: Path to the .env file
        """
        self.schema_path = Path(schema_path)
        self.env_file = Path(env_file)
        self.schema = self._load_schema()
        self._config_cache: Dict[str, Any] = {}

        # Load environment variables
        load_dotenv(self.env_file)

    def _load_schema(self) -> Dict:
        """Load and parse the configuration schema."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with open(self.schema_path, 'r') as f:
            return json.load(f)

    def get_all_fields(self) -> List[Dict]:
        """Get all configuration fields from all sections."""
        all_fields = []
        for section in self.schema.get('sections', []):
            for field in section.get('fields', []):
                field_copy = field.copy()
                field_copy['section_id'] = section['id']
                field_copy['section_title'] = section['title']
                all_fields.append(field_copy)
        return all_fields

    def get_section(self, section_id: str) -> Optional[Dict]:
        """Get a specific configuration section by ID."""
        for section in self.schema.get('sections', []):
            if section['id'] == section_id:
                return section
        return None

    def get_field(self, field_id: str) -> Optional[Dict]:
        """Get a specific field definition by ID."""
        for field in self.get_all_fields():
            if field['id'] == field_id:
                return field
        return None

    def get(self, field_id: str, default: Any = None) -> Any:
        """
        Get a configuration value by field ID.

        Args:
            field_id: The field identifier
            default: Default value if not found

        Returns:
            The configuration value, with type conversion applied
        """
        # Check cache first
        if field_id in self._config_cache:
            return self._config_cache[field_id]

        field = self.get_field(field_id)
        if not field:
            return default

        env_var = field.get('env_var')
        if not env_var:
            return default

        # Get value from environment
        value = os.getenv(env_var)

        # If not found, use default from schema or parameter
        if value is None:
            value = field.get('default', default)

        # Convert to appropriate type
        value = self._convert_type(value, field.get('type'))

        # Cache the value
        self._config_cache[field_id] = value

        return value

    def set(self, field_id: str, value: Any, persist: bool = True) -> bool:
        """
        Set a configuration value.

        Args:
            field_id: The field identifier
            value: The value to set
            persist: Whether to persist to .env file

        Returns:
            True if successful, False otherwise
        """
        field = self.get_field(field_id)
        if not field:
            raise ValueError(f"Unknown field: {field_id}")

        # Validate the value
        validation_result = self.validate_field(field_id, value)
        if not validation_result['valid']:
            raise ValueError(f"Validation failed: {validation_result['errors']}")

        env_var = field.get('env_var')
        if not env_var:
            raise ValueError(f"Field {field_id} has no env_var defined")

        # Convert value to string for environment variable
        str_value = self._value_to_string(value, field.get('type'))

        # Set in environment
        os.environ[env_var] = str_value

        # Update cache
        self._config_cache[field_id] = value

        # Persist to .env file if requested
        if persist:
            self._ensure_env_file()
            set_key(self.env_file, env_var, str_value)

        return True

    def validate_field(self, field_id: str, value: Any) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate a field value against its schema definition.

        Args:
            field_id: The field identifier
            value: The value to validate

        Returns:
            Dict with 'valid' (bool) and 'errors' (list of error messages)
        """
        field = self.get_field(field_id)
        if not field:
            return {'valid': False, 'errors': [f"Unknown field: {field_id}"]}

        errors = []

        # Check required
        if field.get('required') and (value is None or value == ''):
            errors.append(f"{field['label']} is required")
            return {'valid': False, 'errors': errors}

        # Skip validation if value is None/empty and not required
        if value is None or value == '':
            return {'valid': True, 'errors': []}

        validation = field.get('validation', {})

        # Pattern validation (for strings)
        if 'pattern' in validation and isinstance(value, str):
            pattern = validation['pattern']
            if not re.match(pattern, value):
                error_msg = validation.get('errorMessage', f"Value does not match required pattern: {pattern}")
                errors.append(error_msg)

        # Length validation (for strings)
        if isinstance(value, str):
            if 'minLength' in validation and len(value) < validation['minLength']:
                errors.append(f"Minimum length is {validation['minLength']}")
            if 'maxLength' in validation and len(value) > validation['maxLength']:
                errors.append(f"Maximum length is {validation['maxLength']}")

        # Numeric validation
        if isinstance(value, (int, float)):
            if 'min' in validation and value < validation['min']:
                errors.append(f"Minimum value is {validation['min']}")
            if 'max' in validation and value > validation['max']:
                errors.append(f"Maximum value is {validation['max']}")

        # Type validation
        field_type = field.get('type')
        if not self._check_type(value, field_type):
            errors.append(f"Expected type: {field_type}")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def validate_all(self) -> Dict[str, Any]:
        """
        Validate all required configuration fields.

        Returns:
            Dict with validation results for each field
        """
        results = {}

        for field in self.get_all_fields():
            field_id = field['id']
            value = self.get(field_id)
            validation = self.validate_field(field_id, value)

            if not validation['valid']:
                results[field_id] = {
                    'field': field['label'],
                    'section': field['section_title'],
                    'errors': validation['errors'],
                    'required': field.get('required', False)
                }

        return results

    def get_missing_required(self) -> List[Dict]:
        """Get all required fields that are missing or invalid."""
        missing = []

        for field in self.get_all_fields():
            if field.get('required'):
                field_id = field['id']
                value = self.get(field_id)
                validation = self.validate_field(field_id, value)

                if not validation['valid']:
                    missing.append({
                        'id': field_id,
                        'label': field['label'],
                        'section': field['section_title'],
                        'env_var': field.get('env_var'),
                        'errors': validation['errors']
                    })

        return missing

    def export_to_env(self, output_path: Optional[str] = None, include_comments: bool = True) -> str:
        """
        Export current configuration to .env format.

        Args:
            output_path: Optional path to write the .env file
            include_comments: Whether to include comments and section headers

        Returns:
            The .env file content as a string
        """
        lines = []

        if include_comments:
            lines.append("# Office Assistant Configuration")
            lines.append(f"# Generated from schema version {self.schema.get('version', 'unknown')}")
            lines.append("")

        for section in self.schema.get('sections', []):
            if include_comments:
                lines.append(f"# {section['title']}")
                lines.append(f"# {section['description']}")
                lines.append("")

            for field in section.get('fields', []):
                env_var = field.get('env_var')
                if not env_var:
                    continue

                if include_comments:
                    lines.append(f"# {field['label']}")
                    lines.append(f"# {field['description']}")
                    if field.get('required'):
                        lines.append("# REQUIRED")

                # Get current value or default
                value = self.get(field['id'])
                if value is None:
                    value = field.get('default', '')

                # Convert to string
                str_value = self._value_to_string(value, field.get('type'))

                # Add the environment variable
                lines.append(f"{env_var}={str_value}")
                lines.append("")

        content = '\n'.join(lines)

        # Write to file if path provided
        if output_path:
            with open(output_path, 'w') as f:
                f.write(content)

        return content

    def import_from_env(self, env_path: str) -> Dict[str, Any]:
        """
        Import configuration from a .env file.

        Args:
            env_path: Path to the .env file to import

        Returns:
            Dict with import results (imported count, errors, etc.)
        """
        if not Path(env_path).exists():
            raise FileNotFoundError(f".env file not found: {env_path}")

        # Load the environment file
        load_dotenv(env_path, override=True)

        # Clear cache to reload values
        self._config_cache.clear()

        imported = 0
        errors = []

        for field in self.get_all_fields():
            env_var = field.get('env_var')
            if not env_var:
                continue

            value = os.getenv(env_var)
            if value is not None:
                try:
                    # Validate the imported value
                    typed_value = self._convert_type(value, field.get('type'))
                    validation = self.validate_field(field['id'], typed_value)

                    if validation['valid']:
                        imported += 1
                    else:
                        errors.append({
                            'field': field['label'],
                            'env_var': env_var,
                            'errors': validation['errors']
                        })
                except Exception as e:
                    errors.append({
                        'field': field['label'],
                        'env_var': env_var,
                        'errors': [str(e)]
                    })

        return {
            'imported': imported,
            'errors': errors,
            'success': len(errors) == 0
        }

    def get_section_config(self, section_id: str) -> Dict[str, Any]:
        """
        Get all configuration values for a specific section.

        Args:
            section_id: The section identifier

        Returns:
            Dict mapping field IDs to their values
        """
        section = self.get_section(section_id)
        if not section:
            return {}

        config = {}
        for field in section.get('fields', []):
            field_id = field['id']
            config[field_id] = self.get(field_id)

        return config

    def test_connection(self, field_id: str) -> Dict[str, Any]:
        """
        Test a connection for a field that has a test_endpoint defined.

        Args:
            field_id: The field identifier

        Returns:
            Dict with test results
        """
        field = self.get_field(field_id)
        if not field:
            return {'success': False, 'error': 'Field not found'}

        test_endpoint = field.get('test_endpoint')
        if not test_endpoint:
            return {'success': False, 'error': 'No test endpoint defined for this field'}

        # This would integrate with your actual testing infrastructure
        # For now, return a placeholder
        return {
            'success': True,
            'endpoint': test_endpoint,
            'message': 'Test endpoint available (implementation required)'
        }

    def _convert_type(self, value: Any, field_type: Optional[str]) -> Any:
        """Convert value to appropriate Python type based on field type."""
        if value is None or value == '':
            return None

        if field_type == 'number':
            try:
                # Try int first, then float
                if isinstance(value, str) and '.' in value:
                    return float(value)
                return int(value)
            except (ValueError, TypeError):
                return value

        elif field_type == 'boolean':
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)

        elif field_type in ('multiselect', 'tags'):
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                # Assume comma-separated
                return [v.strip() for v in value.split(',') if v.strip()]
            return []

        elif field_type == 'select':
            return str(value) if value is not None else None

        else:  # text, url, secret, etc.
            return str(value) if value is not None else None

    def _value_to_string(self, value: Any, field_type: Optional[str]) -> str:
        """Convert a Python value to string for environment variable storage."""
        if value is None:
            return ''

        if field_type == 'boolean':
            return 'true' if value else 'false'

        elif field_type in ('multiselect', 'tags'):
            if isinstance(value, list):
                return ','.join(str(v) for v in value)
            return str(value)

        else:
            return str(value)

    def _check_type(self, value: Any, field_type: Optional[str]) -> bool:
        """Check if value matches expected field type."""
        if value is None:
            return True

        if field_type == 'number':
            return isinstance(value, (int, float))
        elif field_type == 'boolean':
            return isinstance(value, bool)
        elif field_type in ('multiselect', 'tags'):
            return isinstance(value, list)
        else:
            return isinstance(value, str)

    def _ensure_env_file(self):
        """Ensure .env file exists."""
        if not self.env_file.exists():
            self.env_file.touch()

    def clear_cache(self):
        """Clear the configuration cache."""
        self._config_cache.clear()

    def get_feature_flags(self) -> Dict[str, bool]:
        """Get all feature flag settings."""
        section = self.get_section('feature_flags')
        if not section:
            return {}

        flags = {}
        for field in section.get('fields', []):
            flags[field['id']] = self.get(field['id'], field.get('default', False))

        return flags

    def is_feature_enabled(self, feature_id: str) -> bool:
        """Check if a specific feature is enabled."""
        return bool(self.get(feature_id, False))


# Singleton instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


# Convenience functions
def get_config(field_id: str, default: Any = None) -> Any:
    """Get a configuration value (convenience function)."""
    return get_config_manager().get(field_id, default)


def set_config(field_id: str, value: Any, persist: bool = True) -> bool:
    """Set a configuration value (convenience function)."""
    return get_config_manager().set(field_id, value, persist)


def is_feature_enabled(feature_id: str) -> bool:
    """Check if a feature is enabled (convenience function)."""
    return get_config_manager().is_feature_enabled(feature_id)


if __name__ == "__main__":
    # Example usage and testing
    config = ConfigurationManager()

    print("=== Configuration Manager Test ===\n")

    # Show all sections
    print("Available sections:")
    for section in config.schema.get('sections', []):
        print(f"  - {section['title']} ({section['id']})")

    print("\n=== Missing Required Fields ===")
    missing = config.get_missing_required()
    if missing:
        for item in missing:
            print(f"  - {item['label']} ({item['env_var']})")
            for error in item['errors']:
                print(f"    Error: {error}")
    else:
        print("  All required fields are configured!")

    print("\n=== Feature Flags ===")
    flags = config.get_feature_flags()
    for flag, enabled in flags.items():
        status = "✓ Enabled" if enabled else "✗ Disabled"
        print(f"  {flag}: {status}")

    print("\n=== Sample Configuration Values ===")
    sample_fields = ['ai_temperature', 'max_tokens', 'http_timeout_default']
    for field_id in sample_fields:
        value = config.get(field_id)
        field = config.get_field(field_id)
        print(f"  {field['label']}: {value}")
