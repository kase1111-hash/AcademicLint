"""Configuration classes for AcademicLint."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from academiclint.core.exceptions import ConfigurationError

# Valid values for configuration options
VALID_LEVELS = frozenset({"relaxed", "standard", "strict", "academic"})
VALID_OUTPUT_FORMATS = frozenset({"terminal", "json", "html", "markdown", "github"})


@dataclass
class OutputConfig:
    """Output configuration settings."""

    format: str = "terminal"  # terminal, json, html, markdown, github
    color: bool = True
    show_suggestions: bool = True
    show_examples: bool = True

    def __post_init__(self):
        """Validate output configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate output configuration values."""
        if self.format not in VALID_OUTPUT_FORMATS:
            raise ConfigurationError(
                f"Invalid output format '{self.format}'. "
                f"Valid options: {', '.join(sorted(VALID_OUTPUT_FORMATS))}"
            )


@dataclass
class Config:
    """Linter configuration."""

    level: str = "standard"  # relaxed, standard, strict, academic
    min_density: float = 0.50

    # Domain customization
    domain: Optional[str] = None  # Built-in domain name
    domain_file: Optional[Path] = None  # Custom domain file path
    domain_terms: list[str] = field(default_factory=list)  # Inline domain terms

    # Custom patterns
    additional_weasels: list[str] = field(default_factory=list)
    ignore_patterns: list[str] = field(default_factory=list)

    # Processing options
    sections: Optional[list[str]] = None  # Only analyze these sections

    # Output
    output: OutputConfig = field(default_factory=OutputConfig)

    # Thresholds (derived from level if not set)
    fail_under: Optional[float] = None  # Exit with error if below

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values.

        Raises:
            ConfigurationError: If any configuration value is invalid
        """
        # Validate level
        if self.level not in VALID_LEVELS:
            raise ConfigurationError(
                f"Invalid level '{self.level}'. "
                f"Valid options: {', '.join(sorted(VALID_LEVELS))}"
            )

        # Validate min_density
        if not isinstance(self.min_density, (int, float)):
            raise ConfigurationError(
                f"min_density must be a number, got {type(self.min_density).__name__}"
            )
        if not 0.0 <= self.min_density <= 1.0:
            raise ConfigurationError(
                f"min_density must be between 0.0 and 1.0, got {self.min_density}"
            )

        # Validate fail_under
        if self.fail_under is not None:
            if not isinstance(self.fail_under, (int, float)):
                raise ConfigurationError(
                    f"fail_under must be a number, got {type(self.fail_under).__name__}"
                )
            if not 0.0 <= self.fail_under <= 1.0:
                raise ConfigurationError(
                    f"fail_under must be between 0.0 and 1.0, got {self.fail_under}"
                )

        # Validate domain_file exists if specified
        if self.domain_file is not None:
            path = Path(self.domain_file)
            if not path.exists():
                raise ConfigurationError(f"Domain file not found: {self.domain_file}")
            if not path.is_file():
                raise ConfigurationError(
                    f"Domain file path is not a file: {self.domain_file}"
                )

        # Validate domain_terms is a list of strings
        if not isinstance(self.domain_terms, list):
            raise ConfigurationError("domain_terms must be a list")
        for term in self.domain_terms:
            if not isinstance(term, str):
                raise ConfigurationError(
                    f"All domain_terms must be strings, got {type(term).__name__}"
                )

        # Validate additional_weasels is a list of strings
        if not isinstance(self.additional_weasels, list):
            raise ConfigurationError("additional_weasels must be a list")
        for weasel in self.additional_weasels:
            if not isinstance(weasel, str):
                raise ConfigurationError(
                    f"All additional_weasels must be strings, got {type(weasel).__name__}"
                )

    @classmethod
    def from_file(
        cls, path: Path | str, overrides: Optional[dict] = None
    ) -> "Config":
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
            with path.open() as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")

        if not isinstance(data, dict):
            raise ConfigurationError(
                f"Configuration file must contain a YAML mapping, got {type(data).__name__}"
            )

        if overrides:
            data.update(overrides)

        # Handle nested output config
        output_data = data.pop("output", {})
        output_config = OutputConfig(**output_data) if output_data else OutputConfig()

        try:
            return cls(output=output_config, **data)
        except TypeError as e:
            raise ConfigurationError(f"Unknown configuration option: {e}")

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
