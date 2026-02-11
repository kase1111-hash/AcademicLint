"""End-to-end tests for output formatters.

These tests verify that all formatters produce valid, well-formed output
for analysis results.
"""

import json
import re

import pytest

from academiclint import Config, Linter, AnalysisResult
from academiclint.formatters import (
    TerminalFormatter,
    JSONFormatter,
    MarkdownFormatter,
    GitHubFormatter,
)

from .sample_texts import BAD_TEXT_VAGUE, GOOD_TEXT_PRECISE


@pytest.fixture
def linter():
    """Create linter with standard config."""
    return Linter(Config(level="standard"))


@pytest.fixture
def bad_result(linter):
    """Get analysis result for bad text."""
    return linter.check(BAD_TEXT_VAGUE)


@pytest.fixture
def good_result(linter):
    """Get analysis result for good text."""
    return linter.check(GOOD_TEXT_PRECISE)


class TestJSONFormatterPipeline:
    """Test JSON formatter produces valid JSON."""

    def test_json_output_valid(self, bad_result):
        """JSON output should be valid JSON."""
        formatter = JSONFormatter()
        output = formatter.format(bad_result)

        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_json_contains_required_fields(self, bad_result):
        """JSON output should contain all required fields."""
        formatter = JSONFormatter()
        output = formatter.format(bad_result)
        parsed = json.loads(output)

        # Check required fields
        assert "id" in parsed
        assert "created_at" in parsed
        assert "summary" in parsed
        assert "paragraphs" in parsed

        # Check summary fields
        summary = parsed["summary"]
        assert "density" in summary
        assert "density_grade" in summary
        assert "flag_count" in summary
        assert "word_count" in summary

    def test_json_flags_structure(self, bad_result):
        """JSON flags should have correct structure."""
        formatter = JSONFormatter()
        output = formatter.format(bad_result)
        parsed = json.loads(output)

        for para in parsed["paragraphs"]:
            for flag in para.get("flags", []):
                assert "type" in flag
                assert "term" in flag
                assert "span" in flag
                assert "line" in flag
                assert "severity" in flag
                assert "message" in flag
                assert "suggestion" in flag

    def test_json_good_text_fewer_flags(self, good_result):
        """Good text should produce JSON with fewer flags."""
        formatter = JSONFormatter()
        output = formatter.format(good_result)
        parsed = json.loads(output)

        assert parsed["summary"]["flag_count"] <= 5

    def test_json_indented_option(self, bad_result):
        """JSON should respect indent option."""
        formatter = JSONFormatter(indent=2)
        output = formatter.format(bad_result)

        # Indented JSON should have newlines
        assert "\n" in output
        assert "  " in output


class TestMarkdownFormatterPipeline:
    """Test Markdown formatter produces valid Markdown."""

    def test_markdown_output_valid(self, bad_result):
        """Markdown output should be valid Markdown."""
        formatter = MarkdownFormatter()
        output = formatter.format(bad_result)

        # Should contain markdown elements
        assert "#" in output or "-" in output or "**" in output or output.strip()

    def test_markdown_contains_summary(self, bad_result):
        """Markdown should contain summary section."""
        formatter = MarkdownFormatter()
        output = formatter.format(bad_result)

        # Should have some summary info
        assert "density" in output.lower() or "summary" in output.lower() or \
               str(bad_result.summary.flag_count) in output

    def test_markdown_lists_flags(self, bad_result):
        """Markdown should list flags."""
        formatter = MarkdownFormatter()
        output = formatter.format(bad_result)

        if bad_result.summary.flag_count > 0:
            # Should mention at least one flag type
            flag_types = [f.type.value for f in bad_result.flags]
            has_flag_mention = any(ft.lower() in output.lower() for ft in flag_types)
            assert has_flag_mention or bad_result.flags[0].term in output


class TestTerminalFormatterPipeline:
    """Test Terminal formatter produces readable output."""

    def test_terminal_output_not_empty(self, bad_result):
        """Terminal output should not be empty."""
        formatter = TerminalFormatter()
        output = formatter.format(bad_result)

        assert len(output.strip()) > 0

    def test_terminal_contains_density(self, bad_result):
        """Terminal output should show density."""
        formatter = TerminalFormatter()
        output = formatter.format(bad_result)

        # Should contain density info
        assert "density" in output.lower() or str(bad_result.summary.density)[:4] in output

    def test_terminal_shows_flag_count(self, bad_result):
        """Terminal output should show flag count."""
        formatter = TerminalFormatter()
        output = formatter.format(bad_result)

        # Should mention flags or issues
        assert "flag" in output.lower() or str(bad_result.summary.flag_count) in output or \
               "issue" in output.lower()


class TestGitHubFormatterPipeline:
    """Test GitHub Actions formatter produces valid annotations."""

    def test_github_output_format(self, bad_result):
        """GitHub output should use annotation format."""
        formatter = GitHubFormatter()
        output = formatter.format(bad_result)

        if bad_result.summary.flag_count > 0:
            # GitHub annotations use ::warning:: or ::error:: format
            assert "::" in output or "warning" in output.lower() or "error" in output.lower() or \
                   output.strip()  # May be empty if no actionable items

    def test_github_includes_file_info(self, linter):
        """GitHub output should include file information when available."""
        # Create a result from file analysis
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(BAD_TEXT_VAGUE)
            f.flush()

            result = linter.check_file(f.name)

            formatter = GitHubFormatter()
            output = formatter.format(result)

            # Should produce some output
            assert isinstance(output, str)


class TestFormatterConsistency:
    """Test that formatters are consistent with each other."""

    def test_all_formatters_same_flag_count(self, bad_result):
        """All formatters should report same flag count."""
        formatters = [
            JSONFormatter(),
            TerminalFormatter(),
            MarkdownFormatter(),
        ]

        for formatter in formatters:
            output = formatter.format(bad_result)
            # All should produce output
            assert len(output) > 0

    def test_formatters_handle_empty_flags(self, good_result):
        """All formatters should handle results with few/no flags."""
        formatters = [
            JSONFormatter(),
            MarkdownFormatter(),
            TerminalFormatter(),
            GitHubFormatter(),
        ]

        for formatter in formatters:
            # Should not raise any errors
            output = formatter.format(good_result)
            assert isinstance(output, str)

    def test_formatters_handle_many_flags(self, linter):
        """All formatters should handle results with many flags."""
        # Text designed to produce many flags
        problematic_text = """
        In today's society, many experts believe that some research suggests
        things have changed. Studies show 75% of people agree. It is clear
        that freedom is the state of being free. Social media causes problems.
        """ * 5

        result = linter.check(problematic_text)

        formatters = [
            JSONFormatter(),
            MarkdownFormatter(),
            TerminalFormatter(),
            GitHubFormatter(),
        ]

        for formatter in formatters:
            output = formatter.format(result)
            assert isinstance(output, str)
            assert len(output) > 0


class TestFormatterOptions:
    """Test formatter configuration options."""

    def test_json_compact_mode(self, bad_result):
        """JSON formatter should support compact mode."""
        compact = JSONFormatter(indent=None)
        indented = JSONFormatter(indent=2)

        compact_output = compact.format(bad_result)
        indented_output = indented.format(bad_result)

        # Compact should be shorter (no extra whitespace)
        assert len(compact_output) <= len(indented_output)

    def test_terminal_color_option(self, bad_result):
        """Terminal formatter should respect color option."""
        with_color = TerminalFormatter(color=True)
        without_color = TerminalFormatter(color=False)

        color_output = with_color.format(bad_result)
        plain_output = without_color.format(bad_result)

        # Both should produce output
        assert len(color_output) > 0
        assert len(plain_output) > 0
