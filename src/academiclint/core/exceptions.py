"""Custom exception hierarchy for AcademicLint.

Exception Hierarchy:
    AcademicLintError (base)
    ├── ConfigurationError - Invalid configuration
    ├── ValidationError - Input validation failed
    ├── ParsingError - Document parsing failed
    ├── PipelineError - NLP pipeline errors
    │   ├── ModelNotFoundError - spaCy model not installed
    │   └── ProcessingError - Error during NLP processing
    ├── DetectorError - Error in detector module
    └── FormatterError - Error formatting output
"""


class AcademicLintError(Exception):
    """Base exception for all AcademicLint errors.

    All custom exceptions in AcademicLint inherit from this class,
    making it easy to catch any AcademicLint-specific error.

    Attributes:
        message: Human-readable error description
        details: Optional additional context about the error
    """

    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the full error message."""
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ConfigurationError(AcademicLintError):
    """Raised when configuration is invalid.

    Examples:
        - Invalid level value
        - min_density out of range
        - Domain file not found
        - Invalid YAML syntax
    """

    pass


class ValidationError(AcademicLintError):
    """Raised when input validation fails.

    Examples:
        - Text is None or empty
        - Text exceeds maximum length
        - File path is invalid
        - Unsupported file extension
    """

    pass


class ParsingError(AcademicLintError):
    """Raised when document parsing fails.

    Examples:
        - Invalid Markdown syntax
        - Malformed LaTeX
        - Encoding errors
    """

    def __init__(self, message: str, file_path: str = None, line: int = None):
        self.file_path = file_path
        self.line = line
        details = None
        if file_path:
            details = f"file={file_path}"
            if line:
                details += f", line={line}"
        super().__init__(message, details)


class PipelineError(AcademicLintError):
    """Base class for NLP pipeline errors."""

    pass


class ModelNotFoundError(PipelineError):
    """Raised when a required spaCy model is not installed.

    This error includes instructions for installing the model.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        message = f"spaCy model '{model_name}' not found"
        details = (
            f"Install with: python -m spacy download {model_name}\n"
            f"Or run: academiclint setup"
        )
        super().__init__(message, details)


class ProcessingError(PipelineError):
    """Raised when NLP processing fails.

    Examples:
        - Memory error processing large document
        - Unexpected spaCy error
    """

    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        details = str(original_error) if original_error else None
        super().__init__(message, details)


class DetectorError(AcademicLintError):
    """Raised when a detector encounters an error.

    Attributes:
        detector_name: Name of the detector that failed
    """

    def __init__(self, message: str, detector_name: str = None):
        self.detector_name = detector_name
        details = f"detector={detector_name}" if detector_name else None
        super().__init__(message, details)


class FormatterError(AcademicLintError):
    """Raised when output formatting fails.

    Examples:
        - Template rendering error
        - Invalid format specification
    """

    def __init__(self, message: str, format_name: str = None):
        self.format_name = format_name
        details = f"format={format_name}" if format_name else None
        super().__init__(message, details)


# Re-export for convenience (keep backwards compatibility)
# These were previously defined in other modules
__all__ = [
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
