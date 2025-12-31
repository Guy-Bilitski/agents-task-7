"""MCP Agent - League Competition Agent."""

__version__ = "1.0.0"

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create formatter with timestamp, level, and message
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from uvicorn
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
