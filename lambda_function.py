"""
Main Lambda function entry point that imports the modular implementation.
This file must remain in the root directory for AWS Lambda.
"""

from src.handlers.lambda_handler import lambda_handler

# Lambda handler function that AWS Lambda will call
def handler(event, context):
    """
    Main Lambda handler that delegates to our modular implementation.
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        API Gateway response object
    """
    return lambda_handler(event, context)