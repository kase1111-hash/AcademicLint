"""GitHub Actions formatter for AcademicLint."""

from pathlib import Path

from academiclint.core.result import AnalysisResult, Severity
from academiclint.formatters.base import Formatter


class GitHubFormatter(Formatter):
    """Formatter for GitHub Actions workflow commands."""

    def __init__(self, **kwargs):
        pass

    def format(self, result: AnalysisResult, file_path: str = "input") -> str:
        """Format analysis result as GitHub Actions commands."""
        lines = []

        for flag in result.flags:
            level = self._severity_to_level(flag.severity)
            message = f"{flag.type.value}: \"{flag.term}\" - {flag.suggestion}"

            # GitHub Actions workflow command format
            lines.append(
                f"::{level} file={file_path},line={flag.line},col={flag.column}::{message}"
            )

        # Add error if density is below threshold
        if result.summary.density < 0.5:  # Default threshold
            lines.append(
                f"::error file={file_path}::Density {result.density:.2f} is below threshold 0.50"
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
