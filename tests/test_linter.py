"""Tests for the main Linter class."""

import pytest

from academiclint import Config, Linter
from academiclint.core.result import FlagType


class TestLinter:
    """Tests for Linter class."""

    def test_linter_initialization(self):
        """Test linter can be initialized with default config."""
        linter = Linter()
        assert linter.config is not None
        assert linter.config.level == "standard"

    def test_linter_with_custom_config(self):
        """Test linter can be initialized with custom config."""
        config = Config(level="strict", min_density=0.7)
        linter = Linter(config)
        assert linter.config.level == "strict"
        assert linter.config.min_density == 0.7

    def test_check_returns_result(self, linter, sample_bad_text):
        """Test that check returns an AnalysisResult."""
        result = linter.check(sample_bad_text)
        assert result is not None
        assert result.id.startswith("check_")
        assert result.summary is not None

    def test_check_finds_issues_in_bad_text(self, linter, sample_bad_text):
        """Test that check finds issues in low-quality text."""
        result = linter.check(sample_bad_text)
        assert len(result.flags) > 0
        assert result.density < 0.6

    def test_check_good_text_has_fewer_issues(self, linter, sample_good_text):
        """Test that good text has fewer issues."""
        result = linter.check(sample_good_text)
        # Good text should have higher density
        assert result.density > 0.4

    def test_density_grades(self, linter):
        """Test density grade calculation."""
        assert linter._get_density_grade(0.1) == "vapor"
        assert linter._get_density_grade(0.3) == "thin"
        assert linter._get_density_grade(0.5) == "adequate"
        assert linter._get_density_grade(0.7) == "dense"
        assert linter._get_density_grade(0.9) == "crystalline"


class TestLinterIntegration:
    """Integration tests for Linter."""

    def test_full_analysis_pipeline(self, sample_bad_text):
        """Test complete analysis pipeline."""
        linter = Linter()
        result = linter.check(sample_bad_text)

        # Check result structure
        assert result.id is not None
        assert result.created_at is not None
        assert result.processing_time_ms >= 0
        assert result.summary.word_count > 0
        assert len(result.paragraphs) > 0

    def test_filler_detection(self, linter):
        """Test filler phrase detection."""
        text = "In today's society, it is important to note that things have changed."
        result = linter.check(text)

        filler_flags = [f for f in result.flags if f.type == FlagType.FILLER]
        assert len(filler_flags) > 0

    def test_weasel_detection(self, linter):
        """Test weasel word detection."""
        text = "Many experts believe that this is true. Studies show improvement."
        result = linter.check(text)

        weasel_flags = [f for f in result.flags if f.type == FlagType.WEASEL]
        assert len(weasel_flags) > 0
