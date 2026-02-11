"""AcademicLint - A semantic clarity analyzer for academic writing.

Grammarly checks your spelling. AcademicLint checks your thinking.
"""

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

__version__ = "0.1.0"
__all__ = [
    # Core
    "Linter",
    "Config",
    "OutputConfig",
    # Results
    "AnalysisResult",
    "ParagraphResult",
    "Summary",
    "Flag",
    "FlagType",
    "Severity",
    "Span",
    # Version
    "__version__",
]
