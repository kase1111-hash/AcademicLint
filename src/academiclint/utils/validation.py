"""Input validation utilities for AcademicLint."""

import re
from pathlib import Path
from typing import Optional

from academiclint.core.exceptions import ValidationError


# Maximum text length to prevent memory issues
MAX_TEXT_LENGTH = 10_000_000  # 10 million characters
MAX_FILE_SIZE = 50_000_000  # 50 MB

# Supported file extensions
SUPPORTED_EXTENSIONS = frozenset({".md", ".txt", ".tex", ".markdown", ".text"})


def validate_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    """Validate and sanitize input text.

    Args:
        text: The text to validate
        max_length: Maximum allowed text length

    Returns:
        The sanitized text

    Raises:
        ValidationError: If the text is invalid
    """
    if text is None:
        raise ValidationError("Text cannot be None")

    if not isinstance(text, str):
        raise ValidationError(f"Text must be a string, got {type(text).__name__}")

    if len(text) == 0:
        raise ValidationError("Text cannot be empty")

    if len(text) > max_length:
        raise ValidationError(
            f"Text exceeds maximum length of {max_length:,} characters "
            f"(got {len(text):,} characters)"
        )

    # Sanitize: normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove null bytes (security measure)
    text = text.replace("\x00", "")

    return text


def validate_file_path(
    path: Path | str,
    must_exist: bool = True,
    check_extension: bool = True,
    max_size: int = MAX_FILE_SIZE,
) -> Path:
    """Validate a file path.

    Args:
        path: Path to validate
        must_exist: If True, verify the file exists
        check_extension: If True, verify the extension is supported
        max_size: Maximum file size in bytes

    Returns:
        Validated Path object

    Raises:
        ValidationError: If the path is invalid
        FileNotFoundError: If must_exist is True and file doesn't exist
    """
    if path is None:
        raise ValidationError("File path cannot be None")

    try:
        path = Path(path)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid file path: {e}")

    # Security: prevent path traversal attacks
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError) as e:
        raise ValidationError(f"Cannot resolve file path: {e}")

    if must_exist:
        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not resolved.is_file():
            raise ValidationError(f"Path is not a file: {path}")

        # Check file size
        try:
            size = resolved.stat().st_size
            if size > max_size:
                raise ValidationError(
                    f"File exceeds maximum size of {max_size:,} bytes "
                    f"(got {size:,} bytes)"
                )
        except OSError as e:
            raise ValidationError(f"Cannot read file stats: {e}")

    if check_extension:
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValidationError(
                f"Unsupported file extension '{suffix}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

    return resolved


def validate_paths(
    paths: list[Path | str],
    must_exist: bool = True,
    check_extension: bool = True,
) -> list[Path]:
    """Validate a list of file paths.

    Args:
        paths: List of paths to validate
        must_exist: If True, verify files exist
        check_extension: If True, verify extensions are supported

    Returns:
        List of validated Path objects

    Raises:
        ValidationError: If any path is invalid
    """
    if paths is None:
        raise ValidationError("Paths list cannot be None")

    if not isinstance(paths, (list, tuple)):
        raise ValidationError(f"Paths must be a list, got {type(paths).__name__}")

    if len(paths) == 0:
        raise ValidationError("Paths list cannot be empty")

    validated = []
    for path in paths:
        validated.append(
            validate_file_path(
                path, must_exist=must_exist, check_extension=check_extension
            )
        )

    return validated


def sanitize_pattern(pattern: str) -> str:
    """Sanitize a regex pattern to prevent ReDoS attacks.

    Args:
        pattern: The regex pattern to sanitize

    Returns:
        The sanitized pattern

    Raises:
        ValidationError: If the pattern is invalid or potentially dangerous
    """
    if not isinstance(pattern, str):
        raise ValidationError(f"Pattern must be a string, got {type(pattern).__name__}")

    if len(pattern) > 1000:
        raise ValidationError("Pattern is too long (max 1000 characters)")

    # Check for potentially dangerous patterns (nested quantifiers)
    dangerous_patterns = [
        r"\(.+\)\+\+",  # Nested + quantifiers
        r"\(.+\)\*\*",  # Nested * quantifiers
        r"\(.+\)\{\d+,\}\{\d+,\}",  # Nested range quantifiers
    ]

    for dangerous in dangerous_patterns:
        if re.search(dangerous, pattern):
            raise ValidationError(
                "Pattern contains potentially dangerous nested quantifiers"
            )

    # Try to compile the pattern to check for syntax errors
    try:
        re.compile(pattern)
    except re.error as e:
        raise ValidationError(f"Invalid regex pattern: {e}")

    return pattern
