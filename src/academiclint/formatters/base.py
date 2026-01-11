"""Base formatter interface for AcademicLint."""

from abc import ABC, abstractmethod
from pathlib import Path

from academiclint.core.result import AnalysisResult


class Formatter(ABC):
    """Base class for output formatters."""

    @abstractmethod
    def format(self, result: AnalysisResult) -> str:
        """Format a single analysis result.

        Args:
            result: Analysis result to format

        Returns:
            Formatted string output
        """
        pass

    def format_multiple(self, results: dict[Path, AnalysisResult]) -> str:
        """Format multiple analysis results.

        Args:
            results: Dict mapping file paths to results

        Returns:
            Formatted string output
        """
        outputs = []
        for path, result in results.items():
            outputs.append(f"=== {path} ===\n")
            outputs.append(self.format(result))
            outputs.append("\n")
        return "\n".join(outputs)
