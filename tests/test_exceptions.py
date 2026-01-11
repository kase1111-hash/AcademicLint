"""Tests for custom exception hierarchy."""

import pytest

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


class TestAcademicLintError:
    """Tests for base AcademicLintError."""

    def test_basic_message(self):
        """Test exception with basic message."""
        error = AcademicLintError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details is None

    def test_message_with_details(self):
        """Test exception with message and details."""
        error = AcademicLintError("Test error", details="additional context")
        assert str(error) == "Test error: additional context"
        assert error.message == "Test error"
        assert error.details == "additional context"

    def test_is_exception(self):
        """Test that it inherits from Exception."""
        error = AcademicLintError("Test")
        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self):
        """Test raising and catching the exception."""
        with pytest.raises(AcademicLintError) as exc_info:
            raise AcademicLintError("Test error", "details")
        assert "Test error" in str(exc_info.value)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_inherits_from_base(self):
        """Test inheritance from AcademicLintError."""
        error = ConfigurationError("Invalid level")
        assert isinstance(error, AcademicLintError)
        assert isinstance(error, Exception)

    def test_message(self):
        """Test error message."""
        error = ConfigurationError("Invalid level 'invalid'")
        assert "Invalid level" in str(error)

    def test_with_details(self):
        """Test with additional details."""
        error = ConfigurationError("Invalid config", "must be between 0 and 1")
        assert "Invalid config" in str(error)
        assert "must be between 0 and 1" in str(error)


class TestValidationError:
    """Tests for ValidationError."""

    def test_inherits_from_base(self):
        """Test inheritance from AcademicLintError."""
        error = ValidationError("Text is empty")
        assert isinstance(error, AcademicLintError)

    def test_message(self):
        """Test error message."""
        error = ValidationError("Text exceeds maximum length")
        assert "Text exceeds maximum length" in str(error)


class TestParsingError:
    """Tests for ParsingError."""

    def test_inherits_from_base(self):
        """Test inheritance from AcademicLintError."""
        error = ParsingError("Invalid Markdown")
        assert isinstance(error, AcademicLintError)

    def test_basic_message(self):
        """Test basic error message."""
        error = ParsingError("Invalid syntax")
        assert str(error) == "Invalid syntax"
        assert error.file_path is None
        assert error.line is None

    def test_with_file_path(self):
        """Test error with file path."""
        error = ParsingError("Invalid syntax", file_path="/path/to/file.md")
        assert "Invalid syntax" in str(error)
        assert "file=/path/to/file.md" in str(error)
        assert error.file_path == "/path/to/file.md"

    def test_with_file_and_line(self):
        """Test error with file path and line number."""
        error = ParsingError("Invalid syntax", file_path="/path/file.md", line=42)
        assert "Invalid syntax" in str(error)
        assert "file=/path/file.md" in str(error)
        assert "line=42" in str(error)
        assert error.line == 42


class TestPipelineError:
    """Tests for PipelineError."""

    def test_inherits_from_base(self):
        """Test inheritance from AcademicLintError."""
        error = PipelineError("Pipeline failed")
        assert isinstance(error, AcademicLintError)


class TestModelNotFoundError:
    """Tests for ModelNotFoundError."""

    def test_inherits_from_pipeline_error(self):
        """Test inheritance from PipelineError."""
        error = ModelNotFoundError("en_core_web_lg")
        assert isinstance(error, PipelineError)
        assert isinstance(error, AcademicLintError)

    def test_message_includes_model_name(self):
        """Test that message includes model name."""
        error = ModelNotFoundError("en_core_web_lg")
        assert "en_core_web_lg" in str(error)
        assert error.model_name == "en_core_web_lg"

    def test_includes_install_instructions(self):
        """Test that message includes install instructions."""
        error = ModelNotFoundError("en_core_web_lg")
        assert "python -m spacy download en_core_web_lg" in str(error)
        assert "academiclint setup" in str(error)


class TestProcessingError:
    """Tests for ProcessingError."""

    def test_inherits_from_pipeline_error(self):
        """Test inheritance from PipelineError."""
        error = ProcessingError("Processing failed")
        assert isinstance(error, PipelineError)
        assert isinstance(error, AcademicLintError)

    def test_basic_message(self):
        """Test basic error message."""
        error = ProcessingError("Out of memory")
        assert str(error) == "Out of memory"
        assert error.original_error is None

    def test_with_original_error(self):
        """Test error with original exception."""
        original = ValueError("some error")
        error = ProcessingError("Processing failed", original_error=original)
        assert "Processing failed" in str(error)
        assert "some error" in str(error)
        assert error.original_error is original


class TestDetectorError:
    """Tests for DetectorError."""

    def test_inherits_from_base(self):
        """Test inheritance from AcademicLintError."""
        error = DetectorError("Detector failed")
        assert isinstance(error, AcademicLintError)

    def test_basic_message(self):
        """Test basic error message."""
        error = DetectorError("Pattern matching failed")
        assert str(error) == "Pattern matching failed"
        assert error.detector_name is None

    def test_with_detector_name(self):
        """Test error with detector name."""
        error = DetectorError("Detection failed", detector_name="VaguenessDetector")
        assert "Detection failed" in str(error)
        assert "detector=VaguenessDetector" in str(error)
        assert error.detector_name == "VaguenessDetector"


class TestFormatterError:
    """Tests for FormatterError."""

    def test_inherits_from_base(self):
        """Test inheritance from AcademicLintError."""
        error = FormatterError("Formatting failed")
        assert isinstance(error, AcademicLintError)

    def test_basic_message(self):
        """Test basic error message."""
        error = FormatterError("Template error")
        assert str(error) == "Template error"
        assert error.format_name is None

    def test_with_format_name(self):
        """Test error with format name."""
        error = FormatterError("Rendering failed", format_name="html")
        assert "Rendering failed" in str(error)
        assert "format=html" in str(error)
        assert error.format_name == "html"


class TestExceptionHierarchy:
    """Tests for exception hierarchy and catching."""

    def test_catch_all_with_base(self):
        """Test that all exceptions can be caught with base class."""
        exceptions = [
            ConfigurationError("test"),
            ValidationError("test"),
            ParsingError("test"),
            PipelineError("test"),
            ModelNotFoundError("model"),
            ProcessingError("test"),
            DetectorError("test"),
            FormatterError("test"),
        ]
        for exc in exceptions:
            with pytest.raises(AcademicLintError):
                raise exc

    def test_catch_pipeline_errors(self):
        """Test catching pipeline-related errors."""
        pipeline_errors = [
            ModelNotFoundError("model"),
            ProcessingError("test"),
        ]
        for exc in pipeline_errors:
            with pytest.raises(PipelineError):
                raise exc

    def test_specific_catches_do_not_catch_siblings(self):
        """Test that specific exception types don't catch siblings."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("test")

        # ValidationError should not catch ConfigurationError
        try:
            raise ConfigurationError("test")
        except ValidationError:
            pytest.fail("ValidationError caught ConfigurationError")
        except ConfigurationError:
            pass  # Expected
