"""Tests for semantic density calculation."""

import pytest

from academiclint.core.config import Config
from academiclint.core.result import Flag, FlagType, Severity, Span
from academiclint.density.calculator import (
    calculate_density,
    calculate_flag_penalty,
    lemmatize,
    tokenize,
)


class TestDensityCalculation:
    """Tests for density calculation functions."""

    def test_tokenize(self):
        """Test basic tokenization."""
        tokens = tokenize("Hello world! This is a test.")
        assert len(tokens) == 6
        assert "Hello" in tokens
        assert "test" in tokens

    def test_lemmatize(self):
        """Test basic lemmatization."""
        assert lemmatize("running") == "runn"
        assert lemmatize("walked") == "walk"
        assert lemmatize("happiness") == "happi"

    def test_density_empty_text(self):
        """Test density calculation for empty text."""
        config = Config()
        density = calculate_density("", [], config)
        assert density == 0.0

    def test_density_with_content(self):
        """Test density calculation for text with content."""
        config = Config()
        text = "The quick brown fox jumps over the lazy dog."
        density = calculate_density(text, [], config)
        assert 0.0 <= density <= 1.0

    def test_density_penalty_for_flags(self):
        """Test that flags reduce density."""
        config = Config()
        text = "Society has had a significant impact."

        # Without flags
        density_no_flags = calculate_density(text, [], config)

        # With flags
        flags = [
            Flag(
                type=FlagType.UNDERSPECIFIED,
                term="society",
                span=Span(0, 7),
                line=1,
                column=1,
                severity=Severity.HIGH,
                message="Test",
                suggestion="Test",
            )
        ]
        density_with_flags = calculate_density(text, flags, config)

        assert density_with_flags < density_no_flags

    def test_flag_penalty_calculation(self):
        """Test flag penalty calculation."""
        flags = [
            Flag(
                type=FlagType.UNDERSPECIFIED,
                term="test",
                span=Span(0, 4),
                line=1,
                column=1,
                severity=Severity.LOW,
                message="Test",
                suggestion="Test",
            )
        ]
        penalty = calculate_flag_penalty(flags, 50)
        assert 0 <= penalty <= 0.5

    def test_high_severity_higher_penalty(self):
        """Test that high severity flags have higher penalty."""
        low_flags = [
            Flag(
                type=FlagType.UNDERSPECIFIED,
                term="test",
                span=Span(0, 4),
                line=1,
                column=1,
                severity=Severity.LOW,
                message="Test",
                suggestion="Test",
            )
        ]
        high_flags = [
            Flag(
                type=FlagType.UNDERSPECIFIED,
                term="test",
                span=Span(0, 4),
                line=1,
                column=1,
                severity=Severity.HIGH,
                message="Test",
                suggestion="Test",
            )
        ]

        low_penalty = calculate_flag_penalty(low_flags, 50)
        high_penalty = calculate_flag_penalty(high_flags, 50)

        assert high_penalty > low_penalty
