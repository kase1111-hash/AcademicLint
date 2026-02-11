"""Environment variable and secrets management for AcademicLint.

This module provides secure configuration loading from environment variables
and .env files, with support for secrets managers.

Usage:
    from academiclint.utils.env import load_env, get_env, get_secret

    # Load .env file (optional)
    load_env()

    # Get configuration from environment
    api_key = get_env("ACADEMICLINT_API_KEY")
    level = get_env("ACADEMICLINT_LEVEL", default="standard")

    # Get secrets (with optional secrets manager support)
    sentry_dsn = get_secret("SENTRY_DSN")
"""

import logging
import os
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Environment variable prefix for AcademicLint settings
ENV_PREFIX = "ACADEMICLINT_"

# Loaded environment variables cache
_env_loaded = False


def load_env(
    path: Optional[Path | str] = None,
    override: bool = False,
) -> bool:
    """Load environment variables from a .env file.

    Args:
        path: Path to .env file. If None, searches for .env in current
              directory and parent directories.
        override: If True, override existing environment variables

    Returns:
        True if a .env file was loaded, False otherwise

    Example:
        >>> load_env()  # Load from .env in current directory
        >>> load_env("/path/to/.env")  # Load from specific file
    """
    global _env_loaded

    if path is None:
        # Search for .env file
        path = _find_env_file()
        if path is None:
            logger.debug("No .env file found")
            return False

    path = Path(path)
    if not path.exists():
        logger.debug("Env file not found: %s", path)
        return False

    try:
        _load_env_file(path, override)
        _env_loaded = True
        logger.info("Loaded environment from: %s", path)
        return True
    except Exception as e:
        logger.warning("Failed to load .env file: %s", e)
        return False


def _find_env_file() -> Optional[Path]:
    """Search for .env file in current and parent directories."""
    current = Path.cwd()

    for _ in range(10):  # Limit search depth
        env_file = current / ".env"
        if env_file.exists():
            return env_file

        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def _load_env_file(path: Path, override: bool) -> None:
    """Parse and load a .env file."""
    with path.open() as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse key=value
            if "=" not in line:
                logger.warning("Invalid line %d in .env: %s", line_num, line[:50])
                continue

            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()

            # Remove quotes from value
            if value and value[0] in ('"', "'") and value[-1] == value[0]:
                value = value[1:-1]

            # Set environment variable
            if override or key not in os.environ:
                os.environ[key] = value


def get_env(
    name: str,
    default: Optional[str] = None,
    required: bool = False,
    prefix: bool = True,
) -> Optional[str]:
    """Get an environment variable value.

    Args:
        name: Variable name (without prefix if prefix=True)
        default: Default value if not set
        required: If True, raise error if not set
        prefix: If True, prepend ACADEMICLINT_ prefix

    Returns:
        Environment variable value or default

    Raises:
        ValueError: If required=True and variable is not set

    Example:
        >>> level = get_env("LEVEL", default="standard")
        >>> api_key = get_env("API_KEY", required=True)
    """
    full_name = f"{ENV_PREFIX}{name}" if prefix else name
    value = os.environ.get(full_name)

    if value is None:
        if required:
            raise ValueError(f"Required environment variable not set: {full_name}")
        return default

    return value


def get_env_bool(
    name: str,
    default: bool = False,
    prefix: bool = True,
) -> bool:
    """Get an environment variable as a boolean.

    Truthy values: "true", "1", "yes", "on" (case-insensitive)
    Falsy values: "false", "0", "no", "off", "" (case-insensitive)

    Args:
        name: Variable name
        default: Default value if not set
        prefix: If True, prepend ACADEMICLINT_ prefix

    Returns:
        Boolean value
    """
    value = get_env(name, prefix=prefix)
    if value is None:
        return default

    return value.lower() in ("true", "1", "yes", "on")


def get_env_int(
    name: str,
    default: int = 0,
    prefix: bool = True,
) -> int:
    """Get an environment variable as an integer.

    Args:
        name: Variable name
        default: Default value if not set or invalid
        prefix: If True, prepend ACADEMICLINT_ prefix

    Returns:
        Integer value
    """
    value = get_env(name, prefix=prefix)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid integer value for %s: %s", name, value)
        return default


def get_env_float(
    name: str,
    default: float = 0.0,
    prefix: bool = True,
) -> float:
    """Get an environment variable as a float.

    Args:
        name: Variable name
        default: Default value if not set or invalid
        prefix: If True, prepend ACADEMICLINT_ prefix

    Returns:
        Float value
    """
    value = get_env(name, prefix=prefix)
    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        logger.warning("Invalid float value for %s: %s", name, value)
        return default


def get_env_list(
    name: str,
    default: Optional[list[str]] = None,
    separator: str = ",",
    prefix: bool = True,
) -> list[str]:
    """Get an environment variable as a list.

    Args:
        name: Variable name
        default: Default value if not set
        separator: List item separator
        prefix: If True, prepend ACADEMICLINT_ prefix

    Returns:
        List of strings
    """
    value = get_env(name, prefix=prefix)
    if value is None:
        return default or []

    return [item.strip() for item in value.split(separator) if item.strip()]


def get_secret(
    name: str,
    default: Optional[str] = None,
    secrets_manager: Optional[Callable[[str], Optional[str]]] = None,
) -> Optional[str]:
    """Get a secret value from environment or secrets manager.

    This function first checks the environment, then falls back to
    an optional secrets manager function.

    Args:
        name: Secret name
        default: Default value if not found
        secrets_manager: Optional callable that takes a secret name and
                        returns the secret value (e.g., AWS Secrets Manager)

    Returns:
        Secret value or default

    Example:
        >>> # Simple usage (environment only)
        >>> sentry_dsn = get_secret("SENTRY_DSN")

        >>> # With AWS Secrets Manager
        >>> def aws_get_secret(name):
        ...     import boto3
        ...     client = boto3.client('secretsmanager')
        ...     return client.get_secret_value(SecretId=name)['SecretString']
        >>> api_key = get_secret("API_KEY", secrets_manager=aws_get_secret)
    """
    # First try environment variable
    value = os.environ.get(name)
    if value is not None:
        return value

    # Try secrets manager if provided
    if secrets_manager is not None:
        try:
            value = secrets_manager(name)
            if value is not None:
                return value
        except Exception as e:
            logger.warning("Failed to get secret %s from secrets manager: %s", name, e)

    return default


def mask_secret(value: str, visible_chars: int = 4) -> str:
    """Mask a secret value for safe logging.

    Args:
        value: The secret value to mask
        visible_chars: Number of characters to leave visible at the end

    Returns:
        Masked string (e.g., "****abcd")
    """
    if visible_chars <= 0:
        return "*" * len(value)

    if len(value) < visible_chars:
        return "*" * len(value)

    masked_len = len(value) - visible_chars
    return "*" * masked_len + value[-visible_chars:]


class EnvConfig:
    """Configuration loaded from environment variables.

    This class provides a convenient way to load AcademicLint configuration
    from environment variables with type conversion and defaults.

    Example:
        >>> config = EnvConfig()
        >>> print(config.level)  # From ACADEMICLINT_LEVEL
        >>> print(config.min_density)  # From ACADEMICLINT_MIN_DENSITY
    """

    def __init__(self):
        """Load configuration from environment."""
        load_env()  # Ensure .env is loaded

    @property
    def level(self) -> str:
        """Analysis level (relaxed, standard, strict, academic)."""
        return get_env("LEVEL", default="standard")

    @property
    def min_density(self) -> float:
        """Minimum density threshold."""
        return get_env_float("MIN_DENSITY", default=0.50)

    @property
    def fail_under(self) -> Optional[float]:
        """Fail if density is below this threshold."""
        value = get_env("FAIL_UNDER")
        return float(value) if value else None

    @property
    def domain(self) -> Optional[str]:
        """Domain name for specialized analysis."""
        return get_env("DOMAIN")

    @property
    def output_format(self) -> str:
        """Output format (terminal, json, html, markdown, github)."""
        return get_env("OUTPUT_FORMAT", default="terminal")

    @property
    def color(self) -> bool:
        """Enable colored output."""
        return get_env_bool("COLOR", default=True)

    @property
    def log_level(self) -> str:
        """Logging level."""
        return get_env("LOG_LEVEL", default="WARNING")

    @property
    def sentry_dsn(self) -> Optional[str]:
        """Sentry DSN for error tracking."""
        return get_secret("SENTRY_DSN")

    @property
    def api_host(self) -> str:
        """API server host."""
        return get_env("API_HOST", default="0.0.0.0")

    @property
    def api_port(self) -> int:
        """API server port."""
        return get_env_int("API_PORT", default=8080)

    @property
    def workers(self) -> int:
        """Number of API workers."""
        return get_env_int("WORKERS", default=1)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excludes secrets)."""
        return {
            "level": self.level,
            "min_density": self.min_density,
            "fail_under": self.fail_under,
            "domain": self.domain,
            "output_format": self.output_format,
            "color": self.color,
            "log_level": self.log_level,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "workers": self.workers,
        }
