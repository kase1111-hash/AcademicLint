"""Utility modules for AcademicLint."""

from academiclint.utils.error_reporting import (
    JSONFormatter,
    StructuredLogger,
    capture_exception,
    capture_message,
    init_sentry,
    set_user,
    setup_json_logging,
)
from academiclint.utils.logging import (
    disable_logging,
    enable_logging,
    get_logger,
    set_level,
    setup_logging,
)
from academiclint.utils.patterns import (
    CAUSAL_PATTERNS,
    CITATION_PATTERNS,
    FILLER_PHRASES,
    FUNCTION_WORDS,
    HEDGES,
    NEEDS_CITATION_PATTERNS,
    VAGUE_TERMS,
    WEASEL_PATTERNS,
)
from academiclint.utils.text import extract_context, get_line_column
from academiclint.utils.validation import (
    ValidationError,
    sanitize_pattern,
    validate_file_path,
    validate_paths,
    validate_text,
)

__all__ = [
    # Patterns
    "VAGUE_TERMS",
    "CAUSAL_PATTERNS",
    "CITATION_PATTERNS",
    "WEASEL_PATTERNS",
    "HEDGES",
    "FILLER_PHRASES",
    "FUNCTION_WORDS",
    "NEEDS_CITATION_PATTERNS",
    # Text utilities
    "extract_context",
    "get_line_column",
    # Validation
    "ValidationError",
    "validate_file_path",
    "validate_paths",
    "validate_text",
    "sanitize_pattern",
    # Logging
    "setup_logging",
    "get_logger",
    "set_level",
    "disable_logging",
    "enable_logging",
    # Error reporting
    "init_sentry",
    "capture_exception",
    "capture_message",
    "set_user",
    "StructuredLogger",
    "JSONFormatter",
    "setup_json_logging",
]
