"""Utility modules for AcademicLint."""

from academiclint.utils.patterns import (
    CAUSAL_PATTERNS,
    CITATION_PATTERNS,
    FILLER_PHRASES,
    FUNCTION_WORDS,
    HEDGES,
    NEEDS_CITATION_PATTERNS,
    VAGUE_TERMS,
    WEASEL_PATTERNS,
)
from academiclint.utils.text import extract_context, get_line_column

__all__ = [
    "VAGUE_TERMS",
    "CAUSAL_PATTERNS",
    "CITATION_PATTERNS",
    "WEASEL_PATTERNS",
    "HEDGES",
    "FILLER_PHRASES",
    "FUNCTION_WORDS",
    "NEEDS_CITATION_PATTERNS",
    "extract_context",
    "get_line_column",
]
