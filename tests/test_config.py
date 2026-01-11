"""Tests for configuration handling."""

import tempfile
from pathlib import Path

import pytest

from academiclint.core.config import Config, OutputConfig


class TestConfig:
    """Tests for Config class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        assert config.level == "standard"
        assert config.min_density == 0.50
        assert config.domain is None
        assert config.domain_terms == []

    def test_custom_config(self):
        """Test custom configuration values."""
        config = Config(
            level="strict",
            min_density=0.7,
            domain="philosophy",
            domain_terms=["epistemology", "ontology"],
        )
        assert config.level == "strict"
        assert config.min_density == 0.7
        assert config.domain == "philosophy"
        assert "epistemology" in config.domain_terms

    def test_output_config(self):
        """Test output configuration."""
        output = OutputConfig(format="json", color=False)
        config = Config(output=output)
        assert config.output.format == "json"
        assert config.output.color is False

    def test_level_thresholds(self):
        """Test level threshold retrieval."""
        config = Config(level="academic")
        thresholds = config.get_level_thresholds()
        assert thresholds["min_density"] == 0.75

    def test_config_from_yaml_file(self):
        """Test loading config from YAML file."""
        yaml_content = """
level: strict
min_density: 0.65
domain_terms:
  - epistemology
  - ontology
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = Config.from_file(f.name)
            assert config.level == "strict"
            assert config.min_density == 0.65
            assert "epistemology" in config.domain_terms


class TestOutputConfig:
    """Tests for OutputConfig class."""

    def test_default_output_config(self):
        """Test default output configuration."""
        output = OutputConfig()
        assert output.format == "terminal"
        assert output.color is True
        assert output.show_suggestions is True

    def test_custom_output_config(self):
        """Test custom output configuration."""
        output = OutputConfig(
            format="html",
            color=False,
            show_suggestions=False,
            show_examples=False,
        )
        assert output.format == "html"
        assert output.color is False
        assert output.show_suggestions is False
