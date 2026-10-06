import logging
import traceback
from functools import wraps
from django.db import transaction
from pathlib import Path

def setup_order_logger():
    """Set up a dedicated logger for order processing"""
    logger = logging.getLogger('shop.orders')
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Create file handler for all logs
    file_handler = logging.FileHandler('logs/order_processing.log')
    file_handler.setLevel(logging.DEBUG)
    
    # Create error file handler for error-level logs
    error_handler = logging.FileHandler('logs/order_processing_errors.log')
    error_handler.setLevel(logging.ERROR)
    
    # Create formatters with extended information
    class SafeOrderFormatter(logging.Formatter):
        def format(self, record):
            if not hasattr(record, 'order_id'):
                record.order_id = 'N/A'
            if not hasattr(record, 'user_id'):
                record.user_id = 'N/A'
            if not hasattr(record, 'error_code'):
                record.error_code = 'N/A'
            if not hasattr(record, 'error_details'):
                record.error_details = 'None'
            return super().format(record)

    formatter = SafeOrderFormatter(
        '%(asctime)s - %(levelname)s - OrderID:%(order_id)s - UserID:%(user_id)s - '
        'ErrorCode:%(error_code)s - %(message)s\nDetails: %(error_details)s'
    )
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger

order_logger = setup_order_logger()

class OrderError(Exception):
    """Base exception for order processing errors"""
    def __init__(self, message, code=None, order_id=None, user_id=None, details=None):
        super().__init__(message)
        self.code = code
        self.order_id = order_id
        self.user_id = user_id
        self.details = details

def log_order_processing(func):
    """Decorator to log order processing steps and handle errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[0] if args else None
        user_id = getattr(request.user, 'id', None) if request else None
        order_id = kwargs.get('order_id', None)
        
        extra = {
            'order_id': order_id,
            'user_id': user_id
        }
        
        try:
            order_logger.info(f"Starting {func.__name__}", extra=extra)
            result = func(*args, **kwargs)
            order_logger.info(f"Completed {func.__name__} successfully", extra=extra)
            return result
        except OrderError as e:
            order_logger.error(f"Order processing error: {str(e)}", extra=extra)
            raise
        except Exception as e:
            trace = traceback.format_exc()
            order_logger.error(
                f"Unexpected error in {func.__name__}: {str(e)}\n{trace}",
                extra=extra
            )
            raise
    return wrapper

def log_order_step(step_name):
    """Log individual steps in order processing"""
    def log_step(step_func):
        @wraps(step_func)
        def wrapper(*args, **kwargs):
            extra = {
                'order_id': kwargs.get('order_id'),
                'user_id': kwargs.get('user_id')
            }
            order_logger.debug(f"Starting step: {step_name}", extra=extra)
            try:
                result = step_func(*args, **kwargs)
                order_logger.debug(f"Completed step: {step_name}", extra=extra)
                return result
            except Exception as e:
                order_logger.error(f"Error in step {step_name}: {str(e)}", extra=extra)
                raise
        return wrapper
    return log_step