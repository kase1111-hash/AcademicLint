"""Configuration classes for AcademicLint."""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from academiclint.core.exceptions import ConfigurationError

# Valid values for configuration options
VALID_LEVELS = frozenset({"relaxed", "standard", "strict", "academic"})
VALID_OUTPUT_FORMATS = frozenset({"terminal", "json", "markdown", "github"})


def _validate_unit_interval(name: str, value: object) -> None:
    """Raise ConfigurationError unless value is a number in [0.0, 1.0]."""
    if not isinstance(value, (int, float)):
        raise ConfigurationError(f"{name} must be a number, got {type(value).__name__}")
    if not 0.0 <= value <= 1.0:
        raise ConfigurationError(f"{name} must be between 0.0 and 1.0, got {value}")


def _validate_str_list(name: str, value: object) -> None:
    """Raise ConfigurationError unless value is a list of strings."""
    if not isinstance(value, list):
        raise ConfigurationError(f"{name} must be a list")
    for item in value:
        if not isinstance(item, str):
            raise ConfigurationError(f"All {name} must be strings, got {type(item).__name__}")


@dataclass
class OutputConfig:
    """Output configuration settings."""

    format: str = "terminal"  # terminal, json, markdown, github
    color: bool = True
    show_suggestions: bool = True
    show_examples: bool = True

    def __post_init__(self):
        """Validate output configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate output configuration values."""
        if not isinstance(self.format, str) or self.format not in VALID_OUTPUT_FORMATS:
            raise ConfigurationError(
                f"Invalid output format {self.format!r}. "
                f"Valid options: {', '.join(sorted(VALID_OUTPUT_FORMATS))}"
            )


@dataclass
class Config:
    """Linter configuration."""

    level: str = "standard"  # relaxed, standard, strict, academic
    min_density: float = 0.50

    # Domain customization
    domain: str | None = None  # Built-in domain name
    domain_file: Path | None = None  # Custom domain file path
    domain_terms: list[str] = field(default_factory=list)  # Inline domain terms

    # Custom patterns
    additional_weasels: list[str] = field(default_factory=list)
    ignore_patterns: list[str] = field(default_factory=list)

    # Processing options
    sections: list[str] | None = None  # Only analyze these sections

    # Output
    output: OutputConfig = field(default_factory=OutputConfig)

    # Thresholds (derived from level if not set)
    fail_under: float | None = None  # Exit with error if below

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values.

        Raises:
            ConfigurationError: If any configuration value is invalid
        """
        # Validate level
        if not isinstance(self.level, str) or self.level not in VALID_LEVELS:
            raise ConfigurationError(
                f"Invalid level {self.level!r}. Valid options: {', '.join(sorted(VALID_LEVELS))}"
            )

        if self.domain is not None and not isinstance(self.domain, str):
            raise ConfigurationError(f"domain must be a string, got {type(self.domain).__name__}")

        _validate_unit_interval("min_density", self.min_density)
        if self.fail_under is not None:
            _validate_unit_interval("fail_under", self.fail_under)

        # Validate domain_file exists if specified
        if self.domain_file is not None:
            if not isinstance(self.domain_file, (str, os.PathLike)):
                raise ConfigurationError(
                    f"domain_file must be a path, got {type(self.domain_file).__name__}"
                )
            path = Path(self.domain_file)
            if not path.exists():
                raise ConfigurationError(f"Domain file not found: {self.domain_file}")
            if not path.is_file():
                raise ConfigurationError(f"Domain file path is not a file: {self.domain_file}")

        _validate_str_list("domain_terms", self.domain_terms)
        _validate_str_list("additional_weasels", self.additional_weasels)

    @classmethod
    def from_file(cls, path: Path | str, overrides: dict | None = None) -> "Config":
        """Load configuration from a YAML file.

        Args:
            path: Path to the configuration file
            overrides: Optional dict of values to override

        Returns:
            Config instance with loaded settings

        Raises:
            ConfigurationError: If the file is invalid or values are invalid
            FileNotFoundError: If the config file doesn't exist
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        try:
            with path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}") from e
        except UnicodeDecodeError as e:
            raise ConfigurationError(f"Configuration file is not valid UTF-8: {e}") from e

        if not isinstance(data, dict):
            raise ConfigurationError(
                f"Configuration file must contain a YAML mapping, got {type(data).__name__}"
            )

        if overrides:
            data.update(overrides)

        # Handle nested output config
        output_data = data.pop("output", None) or {}
        if not isinstance(output_data, dict):
            raise ConfigurationError(
                f"'output' must be a YAML mapping, got {type(output_data).__name__}"
            )

        try:
            output_config = OutputConfig(**output_data)
        except TypeError as e:
            raise ConfigurationError(f"Unknown output option: {e}") from e

        try:
            return cls(output=output_config, **data)
        except TypeError as e:
            raise ConfigurationError(f"Unknown configuration option: {e}") from e

    def get_level_thresholds(self) -> dict:
        """Get thresholds based on the configured level.

        Returns:
            Dict with min_density and sensitivity settings for the level
        """
        thresholds = {
            "relaxed": {"min_density": 0.30, "sensitivity": "low"},
            "standard": {"min_density": 0.50, "sensitivity": "medium"},
            "strict": {"min_density": 0.65, "sensitivity": "high"},
            "academic": {"min_density": 0.75, "sensitivity": "comprehensive"},
        }
        return thresholds.get(self.level, thresholds["standard"])

    @classmethod
    def from_env(cls, load_dotenv: bool = True) -> "Config":
        """Load configuration from environment variables.

        Environment variables are prefixed with ACADEMICLINT_ and include:
        - ACADEMICLINT_LEVEL: Analysis level (relaxed, standard, strict, academic)
        - ACADEMICLINT_MIN_DENSITY: Minimum density threshold (0.0-1.0)
        - ACADEMICLINT_FAIL_UNDER: Fail threshold (0.0-1.0)
        - ACADEMICLINT_DOMAIN: Domain name for specialized analysis
        - ACADEMICLINT_OUTPUT_FORMAT: Output format
        - ACADEMICLINT_COLOR: Enable colored output (true/false)

        Args:
            load_dotenv: If True, attempt to load .env file first

        Returns:
            Config instance with settings from environment

        Raises:
            ConfigurationError: If environment values are invalid

        Example:
            >>> # Set environment variables
            >>> os.environ["ACADEMICLINT_LEVEL"] = "strict"
            >>> os.environ["ACADEMICLINT_MIN_DENSITY"] = "0.65"
            >>> config = Config.from_env()
        """
        from academiclint.utils.env import (
            get_env,
            get_env_bool,
            get_env_float,
            load_env,
        )

        if load_dotenv:
            load_env()

        # Build config from environment
        level = get_env("LEVEL", default="standard")
        min_density = get_env_float("MIN_DENSITY", default=0.50)
        domain = get_env("DOMAIN")

        # Fail under is optional
        fail_under_str = get_env("FAIL_UNDER")
        fail_under = float(fail_under_str) if fail_under_str else None

        # Output config from environment
        output_format = get_env("OUTPUT_FORMAT", default="terminal")
        color = get_env_bool("COLOR", default=True)

        output_config = OutputConfig(
            format=output_format,
            color=color,
        )

        return cls(
            level=level,
            min_density=min_density,
            domain=domain,
            fail_under=fail_under,
            output=output_config,
        )
