import logging
import sys
from pathlib import Path

def setup_logger(name, log_file='deskopt.log', level=logging.INFO):
    """
    Setup logger with both file and console handlers

    Args:
        name: Logger name (usually __name__)
        log_file: Path to log file
        level: Logging level

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path('logs')
    log_path.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )

    # File handler - detailed logging
    file_handler = logging.FileHandler(log_path / log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Console handler - simple logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    return logger
