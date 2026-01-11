"""Environment-specific configuration management for AcademicLint.

This module provides environment detection and configuration loading
for development, staging, and production environments.

Usage:
    from academiclint.core.environments import (
        Environment,
        get_environment,
        get_environment_config,
    )

    # Get current environment
    env = get_environment()  # Detects from ACADEMICLINT_ENV

    # Load environment-specific config
    config = get_environment_config()
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Application environment identifiers."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"

    @classmethod
    def from_string(cls, value: str) -> "Environment":
        """Parse environment from string value.

        Args:
            value: Environment name (case-insensitive)

        Returns:
            Environment enum value

        Raises:
            ValueError: If value is not a valid environment
        """
        value_lower = value.lower().strip()

        # Handle common aliases
        aliases = {
            "dev": cls.DEVELOPMENT,
            "develop": cls.DEVELOPMENT,
            "development": cls.DEVELOPMENT,
            "local": cls.DEVELOPMENT,
            "stage": cls.STAGING,
            "staging": cls.STAGING,
            "stg": cls.STAGING,
            "prod": cls.PRODUCTION,
            "production": cls.PRODUCTION,
            "prd": cls.PRODUCTION,
            "test": cls.TEST,
            "testing": cls.TEST,
            "ci": cls.TEST,
        }

        if value_lower in aliases:
            return aliases[value_lower]

        raise ValueError(
            f"Invalid environment '{value}'. "
            f"Valid options: development, staging, production, test"
        )


def get_environment() -> Environment:
    """Detect the current environment from environment variables.

    Checks the following environment variables in order:
    1. ACADEMICLINT_ENV
    2. APP_ENV
    3. ENVIRONMENT
    4. ENV

    Defaults to DEVELOPMENT if none are set.

    Returns:
        Current Environment enum value
    """
    env_vars = ["ACADEMICLINT_ENV", "APP_ENV", "ENVIRONMENT", "ENV"]

    for var in env_vars:
        value = os.environ.get(var)
        if value:
            try:
                env = Environment.from_string(value)
                logger.debug("Detected environment %s from %s", env.value, var)
                return env
            except ValueError:
                logger.warning("Invalid environment value in %s: %s", var, value)

    logger.debug("No environment variable set, defaulting to development")
    return Environment.DEVELOPMENT


def is_development() -> bool:
    """Check if running in development environment."""
    return get_environment() == Environment.DEVELOPMENT


def is_staging() -> bool:
    """Check if running in staging environment."""
    return get_environment() == Environment.STAGING


def is_production() -> bool:
    """Check if running in production environment."""
    return get_environment() == Environment.PRODUCTION


def is_test() -> bool:
    """Check if running in test environment."""
    return get_environment() == Environment.TEST


@dataclass
class AnalysisConfig:
    """Analysis-specific configuration."""

    level: str = "standard"
    min_density: float = 0.50
    fail_under: Optional[float] = None


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers: list[str] = field(default_factory=lambda: ["console"])


@dataclass
class OutputConfig:
    """Output configuration."""

    format: str = "terminal"
    color: bool = True
    show_suggestions: bool = True
    show_examples: bool = True
    verbose: bool = False


@dataclass
class APIConfig:
    """API server configuration."""

    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 1
    reload: bool = False
    debug: bool = False
    cors_origins: list[str] = field(default_factory=list)


@dataclass
class PerformanceConfig:
    """Performance tuning configuration."""

    cache_enabled: bool = True
    cache_ttl: int = 600
    max_workers: int = 4
    timeout: int = 30


@dataclass
class ErrorReportingConfig:
    """Error reporting configuration."""

    sentry_enabled: bool = False
    sentry_dsn: Optional[str] = None
    sentry_environment: Optional[str] = None
    sentry_traces_sample_rate: float = 0.0


@dataclass
class MetricsConfig:
    """Metrics collection configuration."""

    enabled: bool = False
    detailed: bool = False
    export_interval: int = 60


@dataclass
class FeaturesConfig:
    """Feature flags configuration."""

    experimental_detectors: bool = False
    beta_features: bool = False
    debug_mode: bool = False


@dataclass
class EnvironmentConfig:
    """Complete environment-specific configuration.

    This class aggregates all configuration sections for an environment.
    """

    environment: Environment = Environment.DEVELOPMENT
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    api: APIConfig = field(default_factory=APIConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    error_reporting: ErrorReportingConfig = field(default_factory=ErrorReportingConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnvironmentConfig":
        """Create configuration from a dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            EnvironmentConfig instance
        """
        env_str = data.get("environment", "development")
        try:
            environment = Environment.from_string(env_str)
        except ValueError:
            environment = Environment.DEVELOPMENT

        return cls(
            environment=environment,
            analysis=AnalysisConfig(**data.get("analysis", {})),
            logging=LoggingConfig(**data.get("logging", {})),
            output=OutputConfig(**data.get("output", {})),
            api=APIConfig(**data.get("api", {})),
            performance=PerformanceConfig(**data.get("performance", {})),
            error_reporting=ErrorReportingConfig(**data.get("error_reporting", {})),
            metrics=MetricsConfig(**data.get("metrics", {})),
            features=FeaturesConfig(**data.get("features", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        from dataclasses import asdict

        result = asdict(self)
        result["environment"] = self.environment.value
        return result


def _find_config_dir() -> Optional[Path]:
    """Find the config directory.

    Searches in:
    1. ACADEMICLINT_CONFIG_DIR environment variable
    2. ./config relative to current working directory
    3. Package config directory
    """
    # Check environment variable
    config_dir_env = os.environ.get("ACADEMICLINT_CONFIG_DIR")
    if config_dir_env:
        path = Path(config_dir_env)
        if path.is_dir():
            return path

    # Check current working directory
    cwd_config = Path.cwd() / "config"
    if cwd_config.is_dir():
        return cwd_config

    # Check relative to this file (package config)
    pkg_config = Path(__file__).parent.parent.parent.parent / "config"
    if pkg_config.is_dir():
        return pkg_config

    return None


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with values to override

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def _expand_env_vars(data: Any) -> Any:
    """Expand environment variable references in configuration.

    Supports ${VAR} and ${VAR:-default} syntax.

    Args:
        data: Configuration data (dict, list, or scalar)

    Returns:
        Data with environment variables expanded
    """
    if isinstance(data, dict):
        return {k: _expand_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_expand_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Handle ${VAR} and ${VAR:-default} patterns
        if data.startswith("${") and data.endswith("}"):
            inner = data[2:-1]
            if ":-" in inner:
                var_name, default = inner.split(":-", 1)
                return os.environ.get(var_name, default)
            else:
                return os.environ.get(inner, data)
        return data
    else:
        return data


def load_config_file(path: Path) -> dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        path: Path to the configuration file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is invalid YAML
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open() as f:
        data = yaml.safe_load(f) or {}

    return _expand_env_vars(data)


def get_environment_config(
    environment: Optional[Environment] = None,
    config_dir: Optional[Path] = None,
) -> EnvironmentConfig:
    """Load configuration for the specified environment.

    Loads the default configuration and merges with environment-specific
    overrides.

    Args:
        environment: Environment to load config for. If None, auto-detects.
        config_dir: Directory containing config files. If None, auto-detects.

    Returns:
        EnvironmentConfig instance

    Example:
        >>> config = get_environment_config()
        >>> print(config.environment)
        development
        >>> print(config.api.port)
        8080
    """
    if environment is None:
        environment = get_environment()

    if config_dir is None:
        config_dir = _find_config_dir()

    # Start with empty config
    merged_config: dict[str, Any] = {}

    if config_dir:
        # Load default config
        default_path = config_dir / "default.yaml"
        if default_path.exists():
            try:
                merged_config = load_config_file(default_path)
                logger.debug("Loaded default config from %s", default_path)
            except Exception as e:
                logger.warning("Failed to load default config: %s", e)

        # Load environment-specific config
        env_path = config_dir / f"{environment.value}.yaml"
        if env_path.exists():
            try:
                env_config = load_config_file(env_path)
                merged_config = _deep_merge(merged_config, env_config)
                logger.debug("Loaded %s config from %s", environment.value, env_path)
            except Exception as e:
                logger.warning("Failed to load %s config: %s", environment.value, e)

    # Set the environment
    merged_config["environment"] = environment.value

    return EnvironmentConfig.from_dict(merged_config)


def configure_logging(config: Optional[EnvironmentConfig] = None) -> None:
    """Configure logging based on environment configuration.

    Args:
        config: Environment configuration. If None, loads from environment.
    """
    if config is None:
        config = get_environment_config()

    log_config = config.logging

    # Map string level to logging constant
    level = getattr(logging, log_config.level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_config.format,
    )

    # Set package logger level
    package_logger = logging.getLogger("academiclint")
    package_logger.setLevel(level)


# Singleton for cached config
_cached_config: Optional[EnvironmentConfig] = None


def get_config() -> EnvironmentConfig:
    """Get the cached environment configuration.

    This function caches the configuration on first call for performance.
    Use get_environment_config() to force a fresh load.

    Returns:
        Cached EnvironmentConfig instance
    """
    global _cached_config

    if _cached_config is None:
        _cached_config = get_environment_config()

    return _cached_config


def reset_config() -> None:
    """Reset the cached configuration.

    Call this if environment variables change and you need to reload.
    """
    global _cached_config
    _cached_config = None
