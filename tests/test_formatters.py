"""Unit tests for output formatters, using hand-built results."""

from academiclint.core.result import (
    AnalysisResult,
    Flag,
    FlagType,
    ParagraphResult,
    Severity,
    Span,
    Summary,
)
from academiclint.formatters import GitHubFormatter, TerminalFormatter


def make_result(term: str = "led\nto", suggestion: str = "Cite evidence", density: float = 0.4):
    flag = Flag(
        type=FlagType.UNSUPPORTED_CAUSAL,
        term=term,
        span=Span(0, len(term)),
        line=1,
        column=1,
        severity=Severity.MEDIUM,
        message="Causal claim without cited evidence or mechanism",
        suggestion=suggestion,
    )
    paragraph = ParagraphResult(
        index=0, text="This led\nto that.", span=Span(0, 17), density=density, flags=[flag]
    )
    summary = Summary(
        density=density,
        density_grade="thin",
        flag_count=1,
        word_count=4,
        sentence_count=1,
        paragraph_count=1,
        concept_count=2,
        filler_ratio=0.0,
        suggestion_count=0,
    )
    return AnalysisResult(
        id="check_test",
        created_at="2026-01-01T00:00:00+00:00",
        input_length=17,
        processing_time_ms=1,
        summary=summary,
        paragraphs=[paragraph],
    )


class TestGitHubFormatter:
    """Tests for GitHub Actions workflow command output."""

    def test_one_command_per_line(self):
        """A newline in a flag must not split (and so truncate) a command."""
        output = GitHubFormatter().format(make_result(suggestion="Line one\nline two"))

        assert all(line.startswith("::") for line in output.splitlines())
        assert '"led to"' in output
        assert "Line one%0Aline two" in output

    def test_escapes_special_characters(self):
        output = GitHubFormatter().format(
            make_result(suggestion="100% sure"), file_path="docs/a,b:c.md"
        )

        assert "100%25 sure" in output
        assert "file=docs/a%2Cb%3Ac.md," in output

    def test_density_threshold_is_configurable(self):
        result = make_result(density=0.4)

        assert "::error" in GitHubFormatter().format(result)
        assert "::error" not in GitHubFormatter(min_density=0.3).format(result)


class TestTerminalFormatter:
    """Tests for terminal output."""

    def test_line_breaks_collapsed_in_flag_terms(self):
        output = TerminalFormatter().format(make_result())

        assert 'FLAG: "led to"' in output

    def test_quiet_omits_paragraph_details(self):
        output = TerminalFormatter(quiet=True).format(make_result())

        assert "SUMMARY" in output
        assert "FLAG:" not in output
