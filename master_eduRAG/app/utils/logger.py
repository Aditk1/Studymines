"""
Structured logging setup for master_eduRAG.
Provides consistent logging across all modules with proper levels and formatting.
"""

import logging
import os
import sys
from pathlib import Path


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: str = None,
) -> logging.Logger:
    """
    Set up a structured logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to log to (in addition to console)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set level from environment or argument
    log_level = os.getenv("LOG_LEVEL", level).upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level, logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the given name.
    Uses default configuration (INFO level, console output).
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return setup_logger(name)


__all__ = [
    "setup_logger",
    "get_logger",
]
