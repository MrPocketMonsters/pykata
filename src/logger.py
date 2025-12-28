"""Logging configuration and utilities for the PyKata application.

This module provides:
- Centralized logger initialization with settings-based configuration
- Helper functions for structured logging (with context, timers, etc.)
- Consistent log formatting across the application
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional, Any
from functools import wraps

from src.config import settings


def _normalize_level(level_value: Any) -> int:
    """Convert level string or int to valid logging level.

    Args:
        level_value: String (e.g., 'INFO', 'DEBUG') or int logging level

    Returns:
        Valid logging level int, defaults to INFO on invalid input
    """
    if isinstance(level_value, int):
        return level_value

    if isinstance(level_value, str):
        level = int(getattr(logging, level_value.upper(), logging.INFO))
        if isinstance(level, int):
            return level

    return logging.INFO


def _setup_logger() -> logging.Logger:
    """Initialize and configure the root logger.

    Returns:
        Configured logger instance
    """
    # Resolve log level from settings
    resolved_level = _normalize_level(settings.LOG_LEVEL)

    # Configure basic logging
    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    return logging.getLogger(__name__)


# Initialize logger on module import
logger = _setup_logger()
logger.info(f"Logger initialized with level: {settings.LOG_LEVEL}")


@contextmanager
def log_context(context_name: str, **context_vars):
    """Context manager for logging with contextual information.

    Logs entry and exit of a context with optional key-value pairs.

    Args:
        context_name: Name of the context (e.g., 'database_query', 'api_call')
        **context_vars: Additional context variables to log

    Example:
        >>> with log_context('processing', user_id=123, batch_size=50):
        ...     process_data()
        # Logs: Entering processing (user_id=123, batch_size=50)
        # ... processing ...
        # Logs: Exiting processing
    """
    context_str = " ".join(f"{k}={v}" for k, v in context_vars.items())
    if context_str:
        logger.info(f"Entering {context_name} ({context_str})")
    else:
        logger.info(f"Entering {context_name}")

    try:
        yield
    except Exception as e:
        logger.exception(f"Error in {context_name}: {e}")
        raise
    finally:
        logger.info(f"Exiting {context_name}")


@contextmanager
def log_timer(operation_name: str, level: int = logging.INFO):
    """Context manager for timing and logging operations.

    Logs execution time of a code block.

    Args:
        operation_name: Name of the operation being timed
        level: Logging level to use (default: INFO)

    Example:
        >>> with log_timer('database_query'):
        ...     result = db.query()
        # Logs: Starting database_query
        # Logs: database_query completed in 0.234 seconds
    """
    logger.log(level, f"Starting {operation_name}")
    start_time = time.time()

    try:
        yield
    finally:
        elapsed = time.time() - start_time
        logger.log(level, f"{operation_name} completed in {elapsed:.3f} seconds")


def log_call(func):
    """Decorator to log function calls with arguments and return values.

    Logs function entry with arguments, exit with return value, and any exceptions.

    Example:
        >>> @log_call
        ... def process(data, verbose=False):
        ...     return len(data)
        # Logs function entry/exit automatically
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__qualname__
        args_str = ", ".join(repr(arg) for arg in args)
        kwargs_str = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))

        logger.debug(f"Calling {func_name}({all_args})")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func_name} returned {result!r}")
            return result
        except Exception as e:
            logger.exception(f"Exception in {func_name}: {e}")
            raise

    return wrapper


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for a module or component.

    Args:
        name: Logger name (typically __name__ from the calling module).
              If None, returns the root logger.

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Message from my module")
    """
    if name is None:
        return logger
    return logging.getLogger(name)
