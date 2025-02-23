# Setup Guide

## Development Environment Setup

### Prerequisites

1. Python 3.8 or higher
2. pip (Python package installer)
3. git
4. AWS CLI
5. Virtual environment tool (venv)

### Step-by-Step Setup

1. Clone the Repository
```bash
git clone [repository-url]
cd OfficeAssistant
```

2. Create and Activate Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/Mac
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

3. Install Dependencies
```bash
pip install -r requirements.txt
```

4. Set Up Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# Required variables:
# - OPENAI_API_KEY
# - GOOGLE_API_KEY
# - GOOGLE_SEARCH_CX
# - SLACK_BOT_TOKEN
# - OPENWEATHER_KEY
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - AWS_REGION
```

5. Install NLTK Data
```bash
# Python shell
python
>>> import nltk
>>> nltk.download('punkt')
>>> nltk.download('stopwords')
>>> nltk.download('averaged_perceptron_tagger')
```

6. Set Up AWS Resources

Create required AWS resources:

```bash
# Configure AWS CLI
aws configure

# Create S3 buckets
aws s3 mb s3://mariaimagefolder-us
aws s3 mb s3://mariadocsfolder-us

# Create DynamoDB tables
aws dynamodb create-table \
    --table-name staff_history \
    --attribute-definitions AttributeName=chat_id,AttributeType=S AttributeName=sort_key,AttributeType=N \
    --key-schema AttributeName=chat_id,KeyType=HASH AttributeName=sort_key,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

aws dynamodb create-table \
    --table-name maria_history \
    --attribute-definitions AttributeName=chat_id,AttributeType=S AttributeName=sort_key,AttributeType=N \
    --key-schema AttributeName=chat_id,KeyType=HASH AttributeName=sort_key,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

# Additional tables as needed
```

7. Set Up Development Tools
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Testing Setup

1. Install Test Dependencies
```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio
```

2. Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest src/tests/unit/test_config.py
```

## Common Issues and Solutions

### NLTK Data Issues
```python
# If NLTK data is not found, manually create directory and download
import nltk
import os

nltk_data_dir = "/opt/python/nltk_data"
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.append(nltk_data_dir)

nltk.download('punkt', download_dir=nltk_data_dir)
nltk.download('stopwords', download_dir=nltk_data_dir)
nltk.download('averaged_perceptron_tagger', download_dir=nltk_data_dir)
```

### AWS Credentials Issues
```bash
# Check AWS credentials configuration
aws configure list

# Verify AWS credentials file
cat ~/.aws/credentials

# Test AWS access
aws s3 ls
aws dynamodb list-tables
```

### Virtual Environment Issues
```bash
# If venv creation fails, ensure Python is installed correctly
python --version

# If activation fails, check venv directory exists
ls venv

# Recreate venv if needed
rm -rf venv
python -m venv venv
```

## Development Workflow

1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

2. Make Changes
- Follow code style guidelines
- Add tests for new features
- Update documentation

3. Run Tests
```bash
# Run tests
pytest

# Check code coverage
pytest --cov=src --cov-report=html
```

4. Run Linters
```bash
# Run flake8
flake8 src tests

# Run mypy
mypy src
```

5. Commit Changes
```bash
git add .
git commit -m "Description of changes"
```

6. Push Changes
```bash
git push origin feature/your-feature-name
```

## Production Deployment

1. Set Production Environment
```bash
export ENVIRONMENT=production
```

2. Update Configuration
```bash
# Update settings.py with production values
# Update environment variables
```

3. Deploy
```bash
./deploy.sh
```

## Monitoring Setup

1. Configure CloudWatch
```bash
# Set up CloudWatch agent
aws cloudwatch put-metric-alarm \
    --alarm-name high-error-rate \
    --metric-name ErrorCount \
    --namespace CustomMetrics \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --alarm-actions [SNS-TOPIC-ARN]
```

2. Set Up Logging
```bash
# Create log directories
mkdir -p logs/{audit,performance}

# Set permissions
chmod 755 logs
```

3. Configure Metrics
```python
# In your application code
from src.core.performance import performance_monitor

# Record metrics
performance_monitor.record_metric('api_latency', 100, 'timing')
```

## Security Setup

1. Configure Rate Limiting
```python
# Update settings.py with rate limit configuration
RATE_LIMIT_CONFIG = {
    'default': {
        'rate': 100,
        'burst': 200
    },
    'api': {
        'rate': 50,
        'burst': 100
    }
}
```

2. Set Up Audit Logging
```python
# Configure audit logger
from src.core.security import audit_logger

# Log security events
audit_logger.log_security_event(
    'authentication',
    {'user': 'test_user', 'status': 'success'}
)
```

## Additional Resources

- [API Documentation](./API.md)
- [Contributing Guidelines](./CONTRIBUTING.md)
- [Security Guidelines](./SECURITY.md)
- [AWS Setup Guide](./AWS_SETUP.md)