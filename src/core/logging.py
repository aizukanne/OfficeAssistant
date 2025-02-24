import logging
from datetime import datetime
from typing import Optional

def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Sets up a logger with console handler for AWS Lambda.
    
    Args:
        name: Logger name
        level: Logging level
        format_string: Optional format string for log messages
        
    Returns:
        logging.Logger: Configured logger
    """
    if format_string is None:
        format_string = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    
    formatter = logging.Formatter(format_string)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler (goes to CloudWatch in Lambda)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

class ServiceLogger:
    """Base logger class for services."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = setup_logger(service_name)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        print(self._format_message('INFO', message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        print(self._format_message('ERROR', message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        print(self._format_message('WARNING', message, **kwargs))
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        print(self._format_message('DEBUG', message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        print(self._format_message('CRITICAL', message, **kwargs))
    
    def _format_message(self, level: str, message: str, **kwargs) -> str:
        """Format log message with additional context."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"{timestamp} [{level}] [{self.service_name}] {message}"
        if kwargs:
            context = ' '.join(f"{k}={v}" for k, v in kwargs.items())
            formatted_msg += f" [{context}]"
        return formatted_msg

# Create loggers for different services
external_logger = ServiceLogger('external_services')
storage_logger = ServiceLogger('storage_services')
slack_logger = ServiceLogger('slack_services')
openai_logger = ServiceLogger('openai_services')

# Create logger for core functionality
core_logger = ServiceLogger('core')

def log_function_call(logger: ServiceLogger):
    """
    Decorator to log function calls.
    
    Args:
        logger: Logger instance to use
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [DEBUG] [{logger.service_name}] Calling {func_name} args={args} kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [DEBUG] [{logger.service_name}] {func_name} completed successfully")
                return result
            except Exception as e:
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [ERROR] [{logger.service_name}] {func_name} failed error={str(e)}")
                raise
        return wrapper
    return decorator

def log_error(logger: ServiceLogger):
    """
    Decorator to log exceptions.
    
    Args:
        logger: Logger instance to use
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [ERROR] [{logger.service_name}] Error in {func.__name__} error={str(e)} error_type={type(e).__name__}")
                raise
        return wrapper
    return decorator