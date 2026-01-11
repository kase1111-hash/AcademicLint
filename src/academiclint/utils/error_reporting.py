"""Error reporting and monitoring integration for AcademicLint.

This module provides integration with error tracking services like Sentry
and structured logging for log aggregation systems (ELK, Datadog, etc.).

Usage:
    # Initialize Sentry (optional)
    from academiclint.utils.error_reporting import init_sentry, capture_exception

    init_sentry(dsn="https://key@sentry.io/project")

    try:
        result = linter.check(text)
    except Exception as e:
        capture_exception(e, context={"text_length": len(text)})
        raise

    # Structured logging for ELK
    from academiclint.utils.error_reporting import StructuredLogger

    slogger = StructuredLogger("academiclint.analysis")
    slogger.info("analysis_complete", check_id="abc123", density=0.65, flags=5)
"""

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Optional

# Sentry SDK is optional
_sentry_sdk = None
_sentry_initialized = False


def init_sentry(
    dsn: str,
    environment: str = "production",
    release: Optional[str] = None,
    sample_rate: float = 1.0,
    traces_sample_rate: float = 0.0,
    **kwargs,
) -> bool:
    """Initialize Sentry error tracking.

    Args:
        dsn: Sentry DSN (Data Source Name)
        environment: Environment name (production, staging, development)
        release: Release version (defaults to package version)
        sample_rate: Error sampling rate (0.0 to 1.0)
        traces_sample_rate: Performance tracing sample rate
        **kwargs: Additional Sentry SDK options

    Returns:
        True if Sentry was initialized successfully, False otherwise

    Example:
        >>> init_sentry(
        ...     dsn="https://key@sentry.io/project",
        ...     environment="production",
        ...     release="0.1.0"
        ... )
    """
    global _sentry_sdk, _sentry_initialized

    try:
        import sentry_sdk

        _sentry_sdk = sentry_sdk

        # Get release version from package if not provided
        if release is None:
            try:
                from academiclint import __version__

                release = f"academiclint@{__version__}"
            except ImportError:
                release = "academiclint@unknown"

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            sample_rate=sample_rate,
            traces_sample_rate=traces_sample_rate,
            **kwargs,
        )

        _sentry_initialized = True
        return True

    except ImportError:
        logging.getLogger(__name__).warning(
            "sentry-sdk not installed. Install with: pip install sentry-sdk"
        )
        return False
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to initialize Sentry: {e}")
        return False


def capture_exception(
    exception: Exception,
    context: Optional[dict[str, Any]] = None,
    tags: Optional[dict[str, str]] = None,
    level: str = "error",
) -> Optional[str]:
    """Capture an exception and send to Sentry.

    Args:
        exception: The exception to capture
        context: Additional context data
        tags: Tags for filtering in Sentry
        level: Severity level (error, warning, info)

    Returns:
        Sentry event ID if captured, None otherwise

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     capture_exception(e, context={"user_id": "123"})
    """
    if not _sentry_initialized or _sentry_sdk is None:
        # Fall back to logging
        logger = logging.getLogger(__name__)
        logger.error(
            "Exception occurred: %s",
            exception,
            exc_info=True,
            extra={"context": context, "tags": tags},
        )
        return None

    with _sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)

        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        scope.level = level
        return _sentry_sdk.capture_exception(exception)


def capture_message(
    message: str,
    level: str = "info",
    context: Optional[dict[str, Any]] = None,
    tags: Optional[dict[str, str]] = None,
) -> Optional[str]:
    """Capture a message and send to Sentry.

    Args:
        message: The message to capture
        level: Severity level (error, warning, info, debug)
        context: Additional context data
        tags: Tags for filtering

    Returns:
        Sentry event ID if captured, None otherwise
    """
    if not _sentry_initialized or _sentry_sdk is None:
        logger = logging.getLogger(__name__)
        log_func = getattr(logger, level, logger.info)
        log_func(message, extra={"context": context, "tags": tags})
        return None

    with _sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)

        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        return _sentry_sdk.capture_message(message, level=level)


def set_user(user_id: str, email: Optional[str] = None, **kwargs) -> None:
    """Set user context for Sentry.

    Args:
        user_id: Unique user identifier
        email: User email (optional)
        **kwargs: Additional user attributes
    """
    if _sentry_initialized and _sentry_sdk:
        _sentry_sdk.set_user({"id": user_id, "email": email, **kwargs})


class StructuredLogger:
    """Structured logger for log aggregation systems (ELK, Datadog, etc.).

    Outputs JSON-formatted log entries with consistent structure for
    easy parsing and querying in log aggregation systems.

    Example:
        >>> slogger = StructuredLogger("academiclint.api")
        >>> slogger.info("request_received", path="/v1/check", method="POST")
        >>> slogger.error("analysis_failed", error="ValidationError", text_length=50000)
    """

    def __init__(
        self,
        name: str,
        output: str = "stderr",
        include_traceback: bool = True,
    ):
        """Initialize structured logger.

        Args:
            name: Logger name (e.g., "academiclint.api")
            output: Output destination ("stderr", "stdout", or file path)
            include_traceback: Include traceback in error logs
        """
        self.name = name
        self.include_traceback = include_traceback

        if output == "stderr":
            self._stream = sys.stderr
        elif output == "stdout":
            self._stream = sys.stdout
        else:
            self._stream = open(output, "a")

    def _log(self, level: str, event: str, **kwargs) -> None:
        """Write a structured log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "logger": self.name,
            "event": event,
            **kwargs,
        }

        # Add traceback for errors if available
        if level == "error" and self.include_traceback:
            exc_info = sys.exc_info()
            if exc_info[0] is not None:
                entry["traceback"] = "".join(traceback.format_exception(*exc_info))

        self._stream.write(json.dumps(entry) + "\n")
        self._stream.flush()

    def debug(self, event: str, **kwargs) -> None:
        """Log a debug event."""
        self._log("debug", event, **kwargs)

    def info(self, event: str, **kwargs) -> None:
        """Log an info event."""
        self._log("info", event, **kwargs)

    def warning(self, event: str, **kwargs) -> None:
        """Log a warning event."""
        self._log("warning", event, **kwargs)

    def error(self, event: str, **kwargs) -> None:
        """Log an error event."""
        self._log("error", event, **kwargs)

    def critical(self, event: str, **kwargs) -> None:
        """Log a critical event."""
        self._log("critical", event, **kwargs)

    def analysis_complete(
        self,
        check_id: str,
        density: float,
        flag_count: int,
        processing_time_ms: int,
        **kwargs,
    ) -> None:
        """Log analysis completion with standard fields."""
        self.info(
            "analysis_complete",
            check_id=check_id,
            density=density,
            flag_count=flag_count,
            processing_time_ms=processing_time_ms,
            **kwargs,
        )

    def analysis_failed(
        self,
        check_id: str,
        error_type: str,
        error_message: str,
        **kwargs,
    ) -> None:
        """Log analysis failure with standard fields."""
        self.error(
            "analysis_failed",
            check_id=check_id,
            error_type=error_type,
            error_message=error_message,
            **kwargs,
        )


class JSONFormatter(logging.Formatter):
    """JSON formatter for Python logging, compatible with ELK stack.

    Use this formatter with standard Python logging handlers to output
    JSON-formatted logs.

    Example:
        >>> import logging
        >>> handler = logging.StreamHandler()
        >>> handler.setFormatter(JSONFormatter())
        >>> logger = logging.getLogger("academiclint")
        >>> logger.addHandler(handler)
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        entry = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            entry["traceback"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "context"):
            entry["context"] = record.context
        if hasattr(record, "tags"):
            entry["tags"] = record.tags

        return json.dumps(entry)


def setup_json_logging(
    logger_name: str = "academiclint",
    level: str = "INFO",
    output: str = "stderr",
) -> logging.Logger:
    """Set up JSON-formatted logging for ELK/log aggregation.

    Args:
        logger_name: Name of the logger to configure
        level: Log level
        output: Output destination ("stderr", "stdout", or file path)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_json_logging("academiclint", level="DEBUG")
        >>> logger.info("Analysis started", extra={"check_id": "abc123"})
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create handler
    if output == "stderr":
        handler = logging.StreamHandler(sys.stderr)
    elif output == "stdout":
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(output)

    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.propagate = False

    return logger
