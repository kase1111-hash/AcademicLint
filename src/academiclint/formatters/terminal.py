"""Terminal formatter for AcademicLint."""

from collections import Counter

from academiclint.core.result import AnalysisResult, Flag
from academiclint.formatters.base import Formatter


class TerminalFormatter(Formatter):
    """Formatter for terminal/console output."""

    def __init__(self, color: bool = True):
        self.color = color

    def format(self, result: AnalysisResult) -> str:
        """Format analysis result for terminal display."""
        lines = []

        # Format each paragraph with flags
        for para in result.paragraphs:
            if para.flags:
                lines.append(self._format_paragraph(para))
                lines.append("")

        # Format summary
        lines.append(self._format_summary(result))

        return "\n".join(lines)

    def _format_paragraph(self, para) -> str:
        """Format a single paragraph with its flags."""
        lines = []

        # Paragraph header
        lines.append(f"PARAGRAPH {para.index + 1}:")
        lines.append("")

        # Show text excerpt
        text_preview = para.text[:100] + "..." if len(para.text) > 100 else para.text
        lines.append(f'  "{text_preview}"')
        lines.append("")

        # Show flags
        for i, flag in enumerate(para.flags):
            prefix = "└─" if i == len(para.flags) - 1 else "├─"
            lines.append(self._format_flag(flag, prefix))

        # Paragraph density
        lines.append(f"  DENSITY: {para.density:.2f}")

        return "\n".join(lines)

    def _format_flag(self, flag: Flag, prefix: str = "├─") -> str:
        """Format a single flag."""
        lines = []

        # Flag type and term
        lines.append(f"  {prefix} FLAG: \"{flag.term}\" → {flag.type.value}")

        # Message
        lines.append(f"  │   {flag.message}")

        # Suggestion
        lines.append(f"  │   Suggestion: {flag.suggestion}")

        if flag.example_revision:
            lines.append(f"  │   Example: {flag.example_revision}")

        lines.append("  │")

        return "\n".join(lines)

    def _format_summary(self, result: AnalysisResult) -> str:
        """Format the summary section."""
        lines = []

        lines.append("═" * 67)
        lines.append("SUMMARY")
        lines.append("─" * 67)

        lines.append(f"  Overall Density:  {result.density:.2f} ({result.summary.density_grade})")
        lines.append(f"  Total Flags:      {result.summary.flag_count}")
        lines.append(f"  Word Count:       {result.summary.word_count}")
        lines.append("")

        # Flag breakdown
        if result.flags:
            lines.append("  Flag Breakdown:")
            type_counts = Counter(f.type.value for f in result.flags)
            for flag_type, count in type_counts.most_common():
                lines.append(f"    {flag_type}: {count}")

        lines.append("═" * 67)

        # Overall suggestions
        if result.overall_suggestions:
            lines.append("")
            lines.append("SUGGESTIONS:")
            for suggestion in result.overall_suggestions:
                lines.append(f"  • {suggestion}")

        return "\n".join(lines)
