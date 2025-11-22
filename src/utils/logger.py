import logging
import logging.handlers
import sys
import os
from pathlib import Path

# Import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import Config


def setup_logger(name, log_file=None, level=None):
    """
    Setup logger with both file and console handlers

    Args:
        name: Logger name (usually __name__)
        log_file: Path to log file (optional, uses Config default)
        level: Logging level (optional, uses Config default)

    Returns:
        Configured logger instance
    """
    # Use config defaults if not specified
    if log_file is None:
        log_file = Config.get_log_path()
    if level is None:
        level = getattr(logging, Config.LOG_LEVEL)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(Config.LOG_FORMAT)
    simple_formatter = logging.Formatter('%(levelname)s - %(message)s')

    # File handler with rotation - detailed logging
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Console handler - simple logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    return logger
