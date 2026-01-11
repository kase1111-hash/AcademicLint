"""Output formatters for AcademicLint."""

from academiclint.formatters.base import Formatter
from academiclint.formatters.github import GitHubFormatter
from academiclint.formatters.html import HTMLFormatter
from academiclint.formatters.json_ import JSONFormatter
from academiclint.formatters.markdown import MarkdownFormatter
from academiclint.formatters.terminal import TerminalFormatter

__all__ = [
    "Formatter",
    "TerminalFormatter",
    "JSONFormatter",
    "HTMLFormatter",
    "MarkdownFormatter",
    "GitHubFormatter",
    "get_formatter",
]


def get_formatter(format_type: str, **kwargs) -> Formatter:
    """Get a formatter by type.

    Args:
        format_type: Type of formatter (terminal, json, html, markdown, github)
        **kwargs: Additional arguments for the formatter

    Returns:
        Formatter instance
    """
    formatters = {
        "terminal": TerminalFormatter,
        "json": JSONFormatter,
        "html": HTMLFormatter,
        "markdown": MarkdownFormatter,
        "github": GitHubFormatter,
    }

    formatter_class = formatters.get(format_type, TerminalFormatter)
    return formatter_class(**kwargs)
