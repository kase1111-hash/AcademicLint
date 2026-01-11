"""Text utility functions for AcademicLint."""


def get_line_column(text: str, position: int) -> tuple[int, int]:
    """Get line and column number for a character position.

    Args:
        text: The full text
        position: Character position (0-indexed)

    Returns:
        Tuple of (line, column), both 1-indexed
    """
    line = text[:position].count("\n") + 1
    line_start = text.rfind("\n", 0, position) + 1
    column = position - line_start + 1
    return line, column


def extract_context(text: str, start: int, end: int, window: int = 30) -> str:
    """Extract context around a span.

    Args:
        text: The full text
        start: Start position of the span
        end: End position of the span
        window: Number of characters to include on each side

    Returns:
        Context string with the span highlighted
    """
    context_start = max(0, start - window)
    context_end = min(len(text), end + window)

    prefix = text[context_start:start]
    span_text = text[start:end]
    suffix = text[end:context_end]

    # Add ellipsis if truncated
    if context_start > 0:
        prefix = "..." + prefix
    if context_end < len(text):
        suffix = suffix + "..."

    return prefix + span_text + suffix


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences (simple heuristic).

    Args:
        text: The text to split

    Returns:
        List of sentences
    """
    import re

    # Simple sentence splitting on period, question mark, exclamation
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def split_into_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs.

    Args:
        text: The text to split

    Returns:
        List of paragraphs
    """
    paragraphs = text.split("\n\n")
    return [p.strip() for p in paragraphs if p.strip()]
