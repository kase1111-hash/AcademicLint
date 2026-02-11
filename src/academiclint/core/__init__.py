"""Core linting engine for AcademicLint."""

from academiclint.core.config import Config, OutputConfig
from academiclint.core.exceptions import (
    AcademicLintError,
    ConfigurationError,
    DetectorError,
    FormatterError,
    ModelNotFoundError,
    ParsingError,
    PipelineError,
    ProcessingError,
    ValidationError,
)
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
    # Main classes
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
    # Exceptions
    "AcademicLintError",
    "ConfigurationError",
    "ValidationError",
    "ParsingError",
    "PipelineError",
    "ModelNotFoundError",
    "ProcessingError",
    "DetectorError",
    "FormatterError",
]
