"""Tests for input validation utilities."""

import tempfile
from pathlib import Path

import pytest

from academiclint.utils.validation import (
    MAX_FILE_SIZE,
    MAX_TEXT_LENGTH,
    SUPPORTED_EXTENSIONS,
    ValidationError,
    sanitize_pattern,
    validate_file_path,
    validate_paths,
    validate_text,
)


class TestValidateText:
    """Tests for validate_text function."""

    def test_valid_text(self):
        """Test validation of valid text."""
        text = "This is valid text."
        result = validate_text(text)
        assert result == text

    def test_none_raises_error(self):
        """Test that None raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be None"):
            validate_text(None)

    def test_non_string_raises_error(self):
        """Test that non-string raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_text(123)
        with pytest.raises(ValidationError, match="must be a string"):
            validate_text(["list"])

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_text("")

    def test_exceeds_max_length(self):
        """Test that text exceeding max length raises error."""
        long_text = "a" * (MAX_TEXT_LENGTH + 1)
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            validate_text(long_text)

    def test_custom_max_length(self):
        """Test custom max length parameter."""
        text = "a" * 100
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            validate_text(text, max_length=50)
        # Should succeed with higher limit
        result = validate_text(text, max_length=200)
        assert result == text

    def test_normalizes_line_endings(self):
        """Test that line endings are normalized."""
        text_crlf = "line1\r\nline2"
        text_cr = "line1\rline2"

        result_crlf = validate_text(text_crlf)
        result_cr = validate_text(text_cr)

        assert result_crlf == "line1\nline2"
        assert result_cr == "line1\nline2"

    def test_removes_null_bytes(self):
        """Test that null bytes are removed."""
        text = "hello\x00world"
        result = validate_text(text)
        assert result == "helloworld"
        assert "\x00" not in result


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_valid_file(self):
        """Test validation of valid file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            f.flush()
            result = validate_file_path(f.name)
            assert result.exists()
            assert result.is_file()

    def test_none_raises_error(self):
        """Test that None raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be None"):
            validate_file_path(None)

    def test_nonexistent_file(self):
        """Test that nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            validate_file_path("/nonexistent/path/file.txt")

    def test_nonexistent_file_must_exist_false(self):
        """Test that nonexistent file with must_exist=False doesn't raise."""
        # This should not raise even if file doesn't exist
        result = validate_file_path(
            "/some/path/file.txt", must_exist=False, check_extension=True
        )
        assert result is not None

    def test_unsupported_extension(self):
        """Test that unsupported extension raises error."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test")
            f.flush()
            with pytest.raises(ValidationError, match="Unsupported file extension"):
                validate_file_path(f.name)

    def test_supported_extensions(self):
        """Test that all supported extensions work."""
        for ext in SUPPORTED_EXTENSIONS:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(b"test content")
                f.flush()
                result = validate_file_path(f.name)
                assert result.exists()

    def test_extension_check_disabled(self):
        """Test that extension check can be disabled."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"test")
            f.flush()
            # Should not raise with check_extension=False
            result = validate_file_path(f.name, check_extension=False)
            assert result.exists()

    def test_directory_raises_error(self):
        """Test that directory path raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValidationError, match="not a file"):
                validate_file_path(tmpdir)

    def test_accepts_path_object(self):
        """Test that Path object is accepted."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test")
            f.flush()
            path = Path(f.name)
            result = validate_file_path(path)
            assert result.exists()

    def test_returns_resolved_path(self):
        """Test that returned path is resolved."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test")
            f.flush()
            result = validate_file_path(f.name)
            assert result.is_absolute()


class TestValidatePaths:
    """Tests for validate_paths function."""

    def test_valid_paths(self):
        """Test validation of valid path list."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f1:
            f1.write(b"test1")
            f1.flush()
            with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f2:
                f2.write(b"test2")
                f2.flush()
                result = validate_paths([f1.name, f2.name])
                assert len(result) == 2
                assert all(p.exists() for p in result)

    def test_none_raises_error(self):
        """Test that None raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be None"):
            validate_paths(None)

    def test_non_list_raises_error(self):
        """Test that non-list raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a list"):
            validate_paths("not a list")

    def test_empty_list_raises_error(self):
        """Test that empty list raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_paths([])

    def test_tuple_accepted(self):
        """Test that tuple is accepted."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test")
            f.flush()
            result = validate_paths((f.name,))
            assert len(result) == 1

    def test_invalid_path_in_list(self):
        """Test that invalid path in list raises error."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test")
            f.flush()
            with pytest.raises(FileNotFoundError):
                validate_paths([f.name, "/nonexistent/file.txt"])


class TestSanitizePattern:
    """Tests for sanitize_pattern function."""

    def test_valid_pattern(self):
        """Test that valid patterns are returned."""
        pattern = r"\b\w+\b"
        result = sanitize_pattern(pattern)
        assert result == pattern

    def test_non_string_raises_error(self):
        """Test that non-string raises ValidationError."""
        with pytest.raises(ValidationError, match="must be a string"):
            sanitize_pattern(123)

    def test_long_pattern_raises_error(self):
        """Test that long patterns raise error."""
        long_pattern = "a" * 1001
        with pytest.raises(ValidationError, match="too long"):
            sanitize_pattern(long_pattern)

    def test_invalid_regex_raises_error(self):
        """Test that invalid regex raises error."""
        with pytest.raises(ValidationError, match="Invalid regex"):
            sanitize_pattern("[unclosed")

    def test_simple_patterns_work(self):
        """Test that common regex patterns work."""
        patterns = [
            r"\b\w+\b",
            r"[a-z]+",
            r"\d{3}-\d{4}",
            r"^start.*end$",
            r"(group1|group2)",
        ]
        for pattern in patterns:
            result = sanitize_pattern(pattern)
            assert result == pattern

    def test_returns_pattern_unchanged(self):
        """Test that pattern is returned unchanged if valid."""
        pattern = r"\btest\b"
        assert sanitize_pattern(pattern) == pattern


class TestConstants:
    """Tests for validation constants."""

    def test_max_text_length(self):
        """Test MAX_TEXT_LENGTH is reasonable."""
        assert MAX_TEXT_LENGTH > 0
        assert MAX_TEXT_LENGTH == 10_000_000

    def test_max_file_size(self):
        """Test MAX_FILE_SIZE is reasonable."""
        assert MAX_FILE_SIZE > 0
        assert MAX_FILE_SIZE == 50_000_000

    def test_supported_extensions(self):
        """Test SUPPORTED_EXTENSIONS contains expected values."""
        assert ".md" in SUPPORTED_EXTENSIONS
        assert ".txt" in SUPPORTED_EXTENSIONS
        assert ".tex" in SUPPORTED_EXTENSIONS
        assert ".markdown" in SUPPORTED_EXTENSIONS
        assert ".text" in SUPPORTED_EXTENSIONS
        # Should not contain unsupported extensions
        assert ".pdf" not in SUPPORTED_EXTENSIONS
        assert ".docx" not in SUPPORTED_EXTENSIONS
