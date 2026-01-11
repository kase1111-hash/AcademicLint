"""Configuration classes for AcademicLint."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class OutputConfig:
    """Output configuration settings."""

    format: str = "terminal"  # terminal, json, html, markdown, github
    color: bool = True
    show_suggestions: bool = True
    show_examples: bool = True


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
        """
        path = Path(path)
        with path.open() as f:
            data = yaml.safe_load(f) or {}

        if overrides:
            data.update(overrides)

        # Handle nested output config
        output_data = data.pop("output", {})
        output_config = OutputConfig(**output_data) if output_data else OutputConfig()

        return cls(output=output_config, **data)

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
