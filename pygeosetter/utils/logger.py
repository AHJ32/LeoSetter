"""
Logging configuration for PyGeoSetter
"""
import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure application logging"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.expanduser('~'), '.pygeosetter', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Main logger configuration
    logger = logging.getLogger('pygeosetter')
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler (rotating)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'pygeosetter.log'),
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Suppress debug messages from other libraries
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return logger
