"""GitHub Actions formatter for AcademicLint."""

from pathlib import Path

from academiclint.core.result import AnalysisResult, Severity
from academiclint.formatters.base import Formatter


def _escape_data(value: str) -> str:
    """Escape a workflow command message; a raw newline would end the command."""
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(value: str) -> str:
    """Escape a workflow command property value such as a file path."""
    return _escape_data(value).replace(":", "%3A").replace(",", "%2C")


class GitHubFormatter(Formatter):
    """Formatter for GitHub Actions workflow commands."""

    def __init__(self, min_density: float = 0.5, **kwargs):
        self.min_density = min_density

    def format(self, result: AnalysisResult, file_path: str = "input") -> str:
        """Format analysis result as GitHub Actions commands."""
        lines = []
        file_prop = _escape_property(file_path)

        for flag in result.flags:
            level = self._severity_to_level(flag.severity)
            term = " ".join(flag.term.split())
            message = _escape_data(f'{flag.type.value}: "{term}" - {flag.suggestion}')

            # GitHub Actions workflow command format
            lines.append(
                f"::{level} file={file_prop},line={flag.line},col={flag.column}::{message}"
            )

        # Add error if density is below threshold
        if result.summary.density < self.min_density:
            lines.append(
                f"::error file={file_prop}::Density {result.density:.2f} "
                f"is below threshold {self.min_density:.2f}"
            )

        return "\n".join(lines)

    def format_multiple(self, results: dict[Path, AnalysisResult]) -> str:
        """Format multiple results as GitHub Actions commands."""
        lines = []

        for path, result in results.items():
            lines.append(self.format(result, file_path=str(path)))

        return "\n".join(lines)

    def _severity_to_level(self, severity: Severity) -> str:
        """Convert severity to GitHub Actions level."""
        if severity == Severity.HIGH:
            return "error"
        elif severity == Severity.MEDIUM:
            return "warning"
        else:
            return "notice"
