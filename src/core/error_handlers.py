import logging
import json
from typing import Dict, Any, Optional
from decimal import Decimal
from bson import ObjectId
from openai import OpenAIError, BadRequestError
from botocore.exceptions import ClientError
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base exception class for API errors"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class OpenAIAPIError(APIError):
    """Exception for OpenAI API specific errors"""
    pass

class SlackAPIError(APIError):
    """Exception for Slack API specific errors"""
    pass

class DatabaseError(APIError):
    """Exception for database operation errors"""
    pass

class FileOperationError(APIError):
    """Exception for file operation errors"""
    pass

def handle_openai_error(e: OpenAIError) -> Dict[str, Any]:
    """Handle OpenAI API specific errors"""
    if isinstance(e, BadRequestError):
        error = APIError(
            message="Invalid request to OpenAI API",
            status_code=400,
            details={"error_type": "bad_request", "original_error": str(e)}
        )
    else:
        error = APIError(
            message="OpenAI API error",
            status_code=500,
            details={"error_type": "openai_error", "original_error": str(e)}
        )
    
    logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
    return format_error_response(error)

def handle_slack_error(e: RequestException) -> Dict[str, Any]:
    """Handle Slack API specific errors"""
    if hasattr(e, 'response'):
        status_code = e.response.status_code
        try:
            error_details = e.response.json()
        except json.JSONDecodeError:
            error_details = {"error": e.response.text}
    else:
        status_code = 500
        error_details = {"error": str(e)}

    error = APIError(
        message="Slack API error",
        status_code=status_code,
        details={"error_type": "slack_error", "original_error": error_details}
    )
    
    logger.error(f"Slack API error: {str(e)}", exc_info=True)
    return format_error_response(error)

def handle_dynamodb_error(e: ClientError) -> Dict[str, Any]:
    """Handle DynamoDB specific errors"""
    error = APIError(
        message="Database operation error",
        status_code=500,
        details={
            "error_type": "dynamodb_error",
            "error_code": e.response['Error']['Code'],
            "original_error": str(e)
        }
    )
    
    logger.error(f"DynamoDB error: {str(e)}", exc_info=True)
    return format_error_response(error)

def handle_file_operation_error(e: Exception, operation: str) -> Dict[str, Any]:
    """Handle file operation errors"""
    error = APIError(
        message=f"File operation error: {operation}",
        status_code=500,
        details={"error_type": "file_error", "operation": operation, "original_error": str(e)}
    )
    
    logger.error(f"File operation error: {str(e)}", exc_info=True)
    return format_error_response(error)

def format_error_response(error: APIError) -> Dict[str, Any]:
    """Format error response in a consistent structure"""
    response = {
        "success": False,
        "error": {
            "message": error.message,
            "status_code": error.status_code,
            "type": error.__class__.__name__
        }
    }
    
    if error.details:
        response["error"]["details"] = error.details
    
    return response

def decimal_default(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def safe_json_dumps(obj: Any) -> str:
    """Safely convert object to JSON string, handling special types"""
    try:
        return json.dumps(obj, default=decimal_default)
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization error: {str(e)}", exc_info=True)
        return json.dumps({"error": "Could not serialize object"})

# Error handler decorator
def error_handler(error_type=None):
    """Decorator to handle specific types of errors"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except OpenAIError as e:
                return handle_openai_error(e)
            except RequestException as e:
                return handle_slack_error(e)
            except ClientError as e:
                return handle_dynamodb_error(e)
            except Exception as e:
                if error_type:
                    return handle_file_operation_error(e, error_type)
                logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                return format_error_response(APIError(
                    message="An unexpected error occurred",
                    status_code=500,
                    details={"error_type": "unexpected", "original_error": str(e)}
                ))
        return wrapper
    return decorator