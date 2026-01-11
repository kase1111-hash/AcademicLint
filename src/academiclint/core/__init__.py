"""Core linting engine for AcademicLint."""

from academiclint.core.config import Config, OutputConfig
from academiclint.core.environments import (
    Environment,
    EnvironmentConfig,
    get_config,
    get_environment,
    get_environment_config,
    is_development,
    is_production,
    is_staging,
    is_test,
)
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
    # Environment
    "Environment",
    "EnvironmentConfig",
    "get_environment",
    "get_environment_config",
    "get_config",
    "is_development",
    "is_staging",
    "is_production",
    "is_test",
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
