"""Core linting engine for AcademicLint."""

from academiclint.core.config import Config, OutputConfig
from academiclint.core.linter import Linter
from academiclint.core.result import (
    AnalysisResult,
    Flag,
    FlagType,
    ParagraphResult,
    Severity,
    Span,
    Summary,
)

__all__ = [
    "Linter",
    "Config",
    "OutputConfig",
    "AnalysisResult",
    "ParagraphResult",
    "Summary",
    "Flag",
    "FlagType",
    "Severity",
    "Span",
]
