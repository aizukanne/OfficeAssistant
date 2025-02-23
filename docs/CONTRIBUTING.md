# Contributing Guidelines

## Code Style and Standards

### Python Style Guide

1. Follow PEP 8 conventions:
   - Use 4 spaces for indentation
   - Maximum line length of 79 characters
   - Two blank lines before top-level functions and classes
   - One blank line before class methods
   - Use descriptive variable names

2. Type Hints:
   ```python
   from typing import List, Dict, Optional

   def process_data(items: List[str], config: Optional[Dict] = None) -> bool:
       pass
   ```

3. Docstrings:
   ```python
   def function_name(arg1: str, arg2: int) -> bool:
       """
       Brief description of function.
       
       Args:
           arg1: Description of arg1
           arg2: Description of arg2
           
       Returns:
           bool: Description of return value
           
       Raises:
           ValueError: Description of when this error is raised
       """
       pass
   ```

## AWS Lambda Guidelines

### 1. Filesystem Restrictions

- Lambda has a read-only filesystem except for /tmp
- Never write files to the filesystem outside of /tmp
- /tmp is limited to 512MB
- /tmp is not persistent between invocations
- Use S3 for persistent storage needs

Example:
```python
# Bad - Will fail
with open('logs/app.log', 'w') as f:
    f.write('log message')

# Good - Use /tmp if temporary files are needed
with open('/tmp/temp_file.txt', 'w') as f:
    f.write('temporary data')

# Better - Use S3 for persistent storage
s3_client.put_object(
    Bucket='my-bucket',
    Key='logs/app.log',
    Body='log message'
)
```

### 2. Logging Best Practices

- Use print statements for logging (automatically captured by CloudWatch)
- Include timestamp, level, and context in log messages
- Don't create log files
- Structure log messages for easy CloudWatch filtering

Example:
```python
# Bad - Tries to write to filesystem
logger.info("Processing data", file="logs/service.log")  # Will fail

# Good - Uses print for CloudWatch
print(f"{timestamp} [INFO] [service_name] Processing data id={data_id}")
```

### 3. Memory and Performance

- Functions are limited to configured memory (128MB to 10GB)
- CPU scales with memory
- Execution time limit is 15 minutes
- Cold starts can impact performance
- Keep deployment package size small

### 4. Environment Variables

- Use environment variables for configuration
- Don't hardcode sensitive information
- Environment variables persist across invocations
- Can be encrypted using KMS

Example:
```python
import os

api_key = os.getenv('API_KEY')
if not api_key:
    print(f"{timestamp} [ERROR] [service_name] API_KEY not configured")
    raise ValueError("API_KEY environment variable is required")
```

### 5. NLTK Data in Lambda

- NLTK tokenizers (punkt, punkt_tab) are included in Lambda layer at /opt/nltk_data
- Stopwords are included in project root at /var/task/stopwords
- Don't attempt to download NLTK data at runtime
- Verify data exists before using NLTK functions

Project structure:
```
OfficeAssistant/
  ├── lambda_function.py
  ├── src/
  └── stopwords/        # Stopwords at project root
      └── english       # Stopwords file

When deployed to Lambda:
/opt/nltk_data/         # Lambda layer
  └── tokenizers/
      ├── punkt/
      └── punkt_tab/

/var/task/              # Your deployed project
  ├── lambda_function.py
  ├── src/
  └── stopwords/
      └── english
```

Example code:
```python
# Bad - Will fail in Lambda
nltk.download('punkt')  # Can't write to filesystem

# Good - Use provided data locations
nltk.data.path = ['/opt/nltk_data']  # For tokenizers in Lambda layer

try:
    # Verify punkt tokenizer exists
    nltk.data.find('tokenizers/punkt')
    
    # Load stopwords using relative path
    project_root = os.path.dirname(os.path.dirname(__file__))
    stopwords_path = os.path.join(project_root, 'stopwords', 'english')
    with open(stopwords_path, 'r') as f:
        stopwords = [line.strip() for line in f]
except Exception as e:
    print(f"{timestamp} [ERROR] [service_name] Failed to load NLTK data: {str(e)}")
    raise
```

## Development Process

### 1. Setting Up Development Environment

```bash
# Clone repository
git clone [repository-url]
cd OfficeAssistant

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 2. Creating a New Feature

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Implement your changes:
   - Follow code style guidelines
   - Add unit tests
   - Update documentation
   - Add type hints
   - Add proper error handling

3. Run tests:
   ```bash
   pytest
   pytest --cov=src
   ```

4. Run linters:
   ```bash
   flake8 src tests
   mypy src
   ```

### 3. Submitting Changes

1. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a pull request:
   - Use the pull request template
   - Link related issues
   - Provide clear description of changes
   - Include test results

## Testing Guidelines

### 1. Unit Tests

- Write tests for all new code
- Use pytest fixtures for common setup
- Mock external dependencies
- Test edge cases and error conditions

Example:
```python
def test_function_success():
    """Test successful case."""
    result = function()
    assert result == expected_value

def test_function_error():
    """Test error case."""
    with pytest.raises(ValueError):
        function(invalid_input)
```

### 2. Integration Tests

- Test interaction between components
- Use real dependencies when possible
- Clean up test data after tests

Example:
```python
@pytest.mark.integration
def test_service_integration():
    """Test service integration."""
    service = Service()
    result = service.process()
    assert result.status == 'success'
```

## Documentation Guidelines

### 1. Code Documentation

- Add docstrings to all public functions and classes
- Include type hints
- Document exceptions
- Add inline comments for complex logic

### 2. Project Documentation

- Update README.md for significant changes
- Add new documentation files when needed
- Keep setup guide updated
- Document configuration changes

## Error Handling

### 1. Custom Exceptions

- Use custom exceptions for specific error cases
- Inherit from appropriate base exception
- Include helpful error messages

Example:
```python
class ValidationError(BaseError):
    """Raised when validation fails."""
    pass

def validate(data: Dict) -> None:
    if not data:
        raise ValidationError("Data cannot be empty")
```

### 2. Error Logging

- Use print statements for logging in AWS Lambda
- Include timestamp, level, and service name
- Include context in error messages
- Never write to filesystem in Lambda functions

Example:
```python
try:
    process_data(data)
except ValidationError as e:
    print(f"{timestamp} [ERROR] [service_name] Data validation failed error={str(e)} data={data}")
```

## Security Guidelines

### 1. Input Validation

- Validate all input data
- Sanitize user input
- Use request validation decorators

Example:
```python
@validate_request(schema)
def process_input(data: Dict) -> None:
    pass
```

### 2. Authentication

- Use proper authentication mechanisms
- Validate tokens
- Log security events

### 3. Rate Limiting

- Implement rate limiting for APIs
- Log rate limit violations
- Use appropriate limits for different endpoints

## Performance Considerations

### 1. Caching

- Use caching for expensive operations
- Set appropriate TTL values
- Clear cache when data changes

Example:
```python
@cached(ttl=300)
def expensive_operation() -> Dict:
    pass
```

### 2. Database Operations

- Use connection pooling
- Optimize queries
- Use appropriate indexes

### 3. Async Operations

- Use async/await for I/O operations
- Handle concurrent requests properly
- Use connection pools

## Review Process

### 1. Code Review Checklist

- [ ] Follows code style guidelines
- [ ] Includes tests
- [ ] Documentation updated
- [ ] Error handling implemented
- [ ] Security considerations addressed
- [ ] Performance impact considered
- [ ] Lambda filesystem restrictions respected
- [ ] Proper logging implemented for Lambda

### 2. Pull Request Process

1. Create descriptive pull request
2. Link related issues
3. Include test results
4. Address review comments
5. Update based on feedback

## Release Process

### 1. Version Control

- Follow semantic versioning
- Update version numbers
- Create release notes

### 2. Deployment

- Test in staging environment
- Follow deployment checklist
- Monitor for issues
- Verify Lambda configuration

## Getting Help

- Check existing documentation
- Search closed issues
- Ask in appropriate channels
- Provide context when asking questions

## Code of Conduct

- Be respectful and inclusive
- Follow project guidelines
- Help others when possible
- Report inappropriate behavior

## License

This project is licensed under [License Name]. See LICENSE file for details.