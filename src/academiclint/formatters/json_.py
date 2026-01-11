"""JSON formatter for AcademicLint."""

import json
from dataclasses import asdict
from pathlib import Path

from academiclint.core.result import AnalysisResult
from academiclint.formatters.base import Formatter


class JSONFormatter(Formatter):
    """Formatter for JSON output."""

    def __init__(self, indent: int = 2, **kwargs):
        self.indent = indent

    def format(self, result: AnalysisResult) -> str:
        """Format analysis result as JSON."""
        data = self._result_to_dict(result)
        return json.dumps(data, indent=self.indent, default=str)

    def format_multiple(self, results: dict[Path, AnalysisResult]) -> str:
        """Format multiple results as JSON array."""
        data = []
        for path, result in results.items():
            result_dict = self._result_to_dict(result)
            result_dict["file"] = str(path)
            data.append(result_dict)

        return json.dumps(data, indent=self.indent, default=str)

    def _result_to_dict(self, result: AnalysisResult) -> dict:
        """Convert AnalysisResult to dictionary."""
        # Convert flags to serializable format
        paragraphs = []
        for para in result.paragraphs:
            flags = []
            for flag in para.flags:
                flags.append(
                    {
                        "type": flag.type.value,
                        "term": flag.term,
                        "span": {"start": flag.span.start, "end": flag.span.end},
                        "line": flag.line,
                        "column": flag.column,
                        "severity": flag.severity.value,
                        "message": flag.message,
                        "suggestion": flag.suggestion,
                        "example_revision": flag.example_revision,
                        "context": flag.context,
                    }
                )

            paragraphs.append(
                {
                    "index": para.index,
                    "text": para.text,
                    "span": {"start": para.span.start, "end": para.span.end},
                    "density": para.density,
                    "word_count": para.word_count,
                    "sentence_count": para.sentence_count,
                    "flags": flags,
                }
            )

        return {
            "id": result.id,
            "created_at": result.created_at,
            "input_length": result.input_length,
            "processing_time_ms": result.processing_time_ms,
            "summary": {
                "density": result.summary.density,
                "density_grade": result.summary.density_grade,
                "flag_count": result.summary.flag_count,
                "word_count": result.summary.word_count,
                "sentence_count": result.summary.sentence_count,
                "paragraph_count": result.summary.paragraph_count,
                "concept_count": result.summary.concept_count,
                "filler_ratio": result.summary.filler_ratio,
                "suggestion_count": result.summary.suggestion_count,
            },
            "paragraphs": paragraphs,
            "overall_suggestions": result.overall_suggestions,
        }
