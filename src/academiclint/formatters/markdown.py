"""Markdown formatter for AcademicLint."""

from collections import Counter
from pathlib import Path

from academiclint.core.result import AnalysisResult
from academiclint.formatters.base import Formatter


class MarkdownFormatter(Formatter):
    """Formatter for Markdown output."""

    def __init__(self, **kwargs):
        pass

    def format(self, result: AnalysisResult) -> str:
        """Format analysis result as Markdown."""
        lines = []

        lines.append("# AcademicLint Analysis Report")
        lines.append("")
        lines.append(f"**Date**: {result.created_at}")
        lines.append(f"**Density**: {result.density:.2f} ({result.summary.density_grade})")
        lines.append("")

        # Summary table
        lines.append("## Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Overall Density | {result.density:.2f} |")
        lines.append(f"| Total Flags | {result.summary.flag_count} |")
        lines.append(f"| Word Count | {result.summary.word_count} |")
        lines.append(f"| Paragraphs | {result.summary.paragraph_count} |")
        lines.append("")

        # Flags by type
        if result.flags:
            lines.append("## Flags by Type")
            lines.append("")
            type_counts = Counter(f.type.value for f in result.flags)
            for flag_type, count in type_counts.most_common():
                lines.append(f"- {flag_type}: {count}")
            lines.append("")

        # Detailed findings
        lines.append("## Detailed Findings")
        lines.append("")

        for para in result.paragraphs:
            if not para.flags:
                continue

            lines.append(f"### Paragraph {para.index + 1} (Density: {para.density:.2f})")
            lines.append("")

            text_preview = para.text[:200] + "..." if len(para.text) > 200 else para.text
            lines.append(f"> {text_preview}")
            lines.append("")
            lines.append("**Flags**:")
            lines.append("")

            for i, flag in enumerate(para.flags, 1):
                lines.append(f"{i}. **{flag.type.value}**: \"{flag.term}\"")
                lines.append(f"   - {flag.message}")
                lines.append(f"   - *Suggestion*: {flag.suggestion}")
                if flag.example_revision:
                    lines.append(f"   - *Example*: {flag.example_revision}")
                lines.append("")

        # Overall suggestions
        if result.overall_suggestions:
            lines.append("## Overall Suggestions")
            lines.append("")
            for suggestion in result.overall_suggestions:
                lines.append(f"- {suggestion}")

        return "\n".join(lines)

    def format_multiple(self, results: dict[Path, AnalysisResult]) -> str:
        """Format multiple results as Markdown."""
        lines = []
        lines.append("# AcademicLint Analysis Report")
        lines.append("")

        for path, result in results.items():
            lines.append(f"## File: {path}")
            lines.append("")
            # Skip the title line from individual format
            individual = self.format(result)
            individual_lines = individual.split("\n")[2:]  # Skip title and blank line
            lines.extend(individual_lines)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)
