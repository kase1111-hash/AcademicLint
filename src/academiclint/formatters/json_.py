"""JSON formatter for AcademicLint."""

import json
from pathlib import Path

from academiclint.core.result import AnalysisResult
from academiclint.formatters.base import Formatter


class JSONFormatter(Formatter):
    """Formatter for JSON output."""

    def __init__(self, indent: int = 2, **kwargs):
        self.indent = indent

    def format(self, result: AnalysisResult) -> str:
        """Format analysis result as JSON."""
        return json.dumps(result.to_dict(), indent=self.indent, default=str)

    def format_multiple(self, results: dict[Path, AnalysisResult]) -> str:
        """Format multiple results as JSON array."""
        data = []
        for path, result in results.items():
            result_dict = result.to_dict()
            result_dict["file"] = str(path)
            data.append(result_dict)

        return json.dumps(data, indent=self.indent, default=str)
