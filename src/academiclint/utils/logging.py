"""Logging configuration for AcademicLint.

This module provides centralized logging configuration with support for
multiple output formats and log levels.

Usage:
    from academiclint.utils.logging import setup_logging, get_logger

    # Setup logging (typically at application start)
    setup_logging(level="INFO", format="detailed")

    # Get a logger for your module
    logger = get_logger(__name__)
    logger.info("Starting analysis")
"""

import logging
import sys
from typing import Optional

# Default format strings
FORMATS = {
    "simple": "%(levelname)s: %(message)s",
    "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "debug": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    "json": '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
}

# Package logger
_package_logger = logging.getLogger("academiclint")


def setup_logging(
    level: str = "WARNING",
    format: str = "simple",
    output: str = "stderr",
    filename: Optional[str] = None,
) -> None:
    """Configure logging for AcademicLint.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Format style (simple, detailed, debug, json)
        output: Output destination (stderr, stdout, file)
        filename: Log file path (required if output is "file")

    Example:
        >>> setup_logging(level="DEBUG", format="detailed")
        >>> setup_logging(level="INFO", output="file", filename="academiclint.log")
    """
    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.WARNING)

    # Get format string
    format_string = FORMATS.get(format, FORMATS["simple"])

    # Create formatter
    formatter = logging.Formatter(format_string)

    # Remove existing handlers
    _package_logger.handlers.clear()

    # Create handler based on output type
    if output == "file" and filename:
        handler = logging.FileHandler(filename)
    elif output == "stdout":
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.StreamHandler(sys.stderr)

    handler.setFormatter(formatter)
    _package_logger.addHandler(handler)
    _package_logger.setLevel(numeric_level)

    # Don't propagate to root logger
    _package_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance configured as child of academiclint logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing document")
    """
    if name.startswith("academiclint"):
        return logging.getLogger(name)
    return logging.getLogger(f"academiclint.{name}")


def set_level(level: str) -> None:
    """Set the log level for all AcademicLint loggers.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    _package_logger.setLevel(numeric_level)


def disable_logging() -> None:
    """Disable all AcademicLint logging.

    Useful for library usage where the host application controls logging.
    """
    _package_logger.disabled = True


def enable_logging() -> None:
    """Re-enable AcademicLint logging."""
    _package_logger.disabled = False


# Configure default logging (quiet by default for library use)
setup_logging(level="WARNING", format="simple")
