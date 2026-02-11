"""Utility modules for AcademicLint."""

from academiclint.utils.env import (
    EnvConfig,
    get_env,
    get_env_bool,
    get_env_float,
    get_env_int,
    get_env_list,
    get_secret,
    load_env,
    mask_secret,
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
    # Environment & Configuration
    "load_env",
    "get_env",
    "get_env_bool",
    "get_env_int",
    "get_env_float",
    "get_env_list",
    "get_secret",
    "mask_secret",
    "EnvConfig",
    # Logging
    "setup_logging",
    "get_logger",
    "set_level",
    "disable_logging",
    "enable_logging",
]
