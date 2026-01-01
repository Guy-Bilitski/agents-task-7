"""League infrastructure package.

Contains the League Manager and Referee for running parity game competitions.
"""
import logging

__version__ = "1.0.0"


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
