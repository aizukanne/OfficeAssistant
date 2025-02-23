# Office Assistant Documentation

## Overview

The Office Assistant is a comprehensive system that provides various services including external API integration, storage management, messaging, and AI capabilities. The system follows a service-oriented architecture with proper error handling, logging, security measures, and performance optimizations.

## Architecture

### Core Components

1. Configuration Management (`src/config/`)
   - `settings.py`: Centralized configuration
   - Environment variables validation
   - API endpoints and credentials

2. Core Infrastructure (`src/core/`)
   - `exceptions.py`: Custom exception hierarchy
   - `logging.py`: Comprehensive logging system
   - `security.py`: Security measures
   - `performance.py`: Performance optimizations

3. Services (`src/services/`)
   - `interfaces.py`: Service interfaces
   - `external_services.py`: External API integration
   - `storage_service.py`: Storage management
   - `slack_service.py`: Slack integration
   - `openai_service.py`: OpenAI integration
   - `odoo_service.py`: Odoo integration

4. Utilities (`src/utils/`)
   - `text_processing.py`: Text processing utilities
   - `tools.py`: Tool definitions

## Setup

### Prerequisites

- Python 3.8+
- AWS credentials
- API keys for:
  - OpenAI
  - Google
  - Slack
  - OpenWeather

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd OfficeAssistant
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

### Environment Variables

Required environment variables:
- `OPENAI_API_KEY`: OpenAI API key
- `GOOGLE_API_KEY`: Google API key
- `GOOGLE_SEARCH_CX`: Google Custom Search CX
- `SLACK_BOT_TOKEN`: Slack bot token
- `OPENWEATHER_KEY`: OpenWeather API key
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region

### AWS Resources

Required AWS resources:
- S3 buckets for file storage
- DynamoDB tables for data storage

## Security

### Rate Limiting

The system implements rate limiting using a token bucket algorithm:
```python
@rate_limit(tokens=1)
def rate_limited_function():
    pass
```

### Request Validation

Input validation and sanitization:
```python
@validate_request(schema)
def validated_function(data):
    pass
```

### Audit Logging

Security event logging:
```python
@audit_log('event_type')
def audited_function():
    pass
```

## Performance

### Caching

LRU cache implementation:
```python
@cached(ttl=300)
def cached_function():
    pass
```

### Connection Pooling

Connection pool usage:
```python
async with connection_pool.get_connection() as conn:
    await conn.execute(query)
```

### Request Queue

Priority-based request queuing:
```python
await request_queue.enqueue(request, priority='high')
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest src/tests/unit/test_config.py

# Run with coverage
pytest --cov=src
```

### Test Structure

- `src/tests/conftest.py`: Test fixtures
- `src/tests/unit/`: Unit tests
- `src/tests/integration/`: Integration tests

## Development

### Adding a New Service

1. Define interface in `src/services/interfaces.py`
2. Implement service class
3. Add to service factory
4. Create unit tests
5. Update documentation

### Code Style

- Follow PEP 8
- Use type hints
- Write comprehensive docstrings
- Add unit tests for new code

## Deployment

### Production Setup

1. Set up environment:
```bash
export ENVIRONMENT=production
```

2. Configure AWS resources:
```bash
terraform apply
```

3. Deploy application:
```bash
./deploy.sh
```

### Monitoring

- Use CloudWatch for AWS resources
- Monitor application metrics via `PerformanceMonitor`
- Check audit logs for security events

## Troubleshooting

### Common Issues

1. Rate Limiting
   - Check `RateLimitError` exceptions
   - Adjust rate limits in configuration

2. Connection Issues
   - Verify AWS credentials
   - Check network connectivity
   - Review connection pool settings

3. Performance Issues
   - Monitor cache hit rates
   - Check connection pool utilization
   - Review request queue metrics

### Logging

- Application logs in `logs/`
- Audit logs in `logs/audit/`
- Performance metrics in `logs/performance/`

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Create pull request

### Pull Request Guidelines

- Follow code style
- Include tests
- Update documentation
- Add to changelog

## License

[License details here]