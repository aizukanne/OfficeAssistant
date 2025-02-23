import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Sets up a logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Optional log file path
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
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log_file is specified
    if log_file:
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

class ServiceLogger:
    """Base logger class for services."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = setup_logger(
            service_name,
            f"logs/{service_name}/{datetime.now().strftime('%Y-%m-%d')}.log"
        )
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(self._format_message(message, **kwargs))
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format log message with additional context."""
        if kwargs:
            context = ' '.join(f"{k}={v}" for k, v in kwargs.items())
            return f"{message} [{context}]"
        return message

# Create loggers for different services
external_logger = ServiceLogger('external_services')
storage_logger = ServiceLogger('storage_services')
slack_logger = ServiceLogger('slack_services')
openai_logger = ServiceLogger('openai_services')
odoo_logger = ServiceLogger('odoo_services')

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
            logger.debug(f"Calling {func_name}", args=args, kwargs=kwargs)
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func_name} failed", error=str(e))
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
                logger.error(
                    f"Error in {func.__name__}",
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        return wrapper
    return decorator