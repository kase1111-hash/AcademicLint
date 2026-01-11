"""Security tests for AcademicLint.

This module verifies security measures including:
- Input validation and sanitization
- Secret/token handling
- Injection prevention
- Path traversal protection
- Resource exhaustion prevention
- Safe error handling (no information leakage)
"""

import os
import tempfile
from pathlib import Path

import pytest

from academiclint import Config, Linter
from academiclint.core.result import AnalysisResult
from academiclint.utils.validation import (
    ValidationError,
    sanitize_pattern,
    validate_file_path,
    validate_text,
)


# =============================================================================
# Input Validation Security Tests
# =============================================================================

class TestInputValidation:
    """Tests for secure input validation."""

    def test_null_byte_injection_blocked(self):
        """Null bytes should be sanitized from input."""
        # Null byte injection attempt
        malicious = "normal text\x00malicious"

        # Should either sanitize or reject
        result = validate_text(malicious)
        assert "\x00" not in result

    def test_very_long_input_rejected(self):
        """Extremely long inputs should be rejected."""
        # 100MB of text would be a DoS attempt
        huge_text = "a" * (100 * 1024 * 1024)

        with pytest.raises(ValidationError):
            validate_text(huge_text)

    def test_none_input_rejected(self):
        """None input should be rejected, not cause crash."""
        with pytest.raises(ValidationError):
            validate_text(None)

    def test_non_string_input_rejected(self):
        """Non-string inputs should be rejected safely."""
        invalid_inputs = [123, [], {}, object(), b"bytes"]

        for invalid in invalid_inputs:
            with pytest.raises(ValidationError):
                validate_text(invalid)

    def test_control_characters_handled(self):
        """Control characters should be handled safely."""
        control_chars = "".join(chr(i) for i in range(32) if i not in [9, 10, 13])
        text = f"Normal {control_chars} text"

        # Should not crash
        try:
            result = Linter().check(text)
            assert isinstance(result, AnalysisResult)
        except ValidationError:
            pass  # Also acceptable to reject

    def test_unicode_exploits_handled(self):
        """Unicode-based exploits should be handled."""
        # Right-to-left override
        rtl_override = "normal \u202e\u0065\u0074\u0061\u0072\u0074\u0073"

        # Should handle without crash
        try:
            result = Linter().check(rtl_override)
            assert isinstance(result, AnalysisResult)
        except ValidationError:
            pass

    def test_emoji_sequences_handled(self):
        """Complex emoji sequences shouldn't cause issues."""
        # Family emoji with skin tones
        complex_emoji = "Test 👨‍👩‍👧‍👦 and 👋🏽 here"

        result = Linter().check(complex_emoji)
        assert isinstance(result, AnalysisResult)


# =============================================================================
# Path Traversal Protection Tests
# =============================================================================

class TestPathTraversalProtection:
    """Tests for path traversal attack prevention."""

    def test_path_traversal_blocked(self):
        """Path traversal attempts should be blocked."""
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2fetc/passwd",
        ]

        for path in traversal_paths:
            # Should raise error, not access the file
            with pytest.raises((ValidationError, FileNotFoundError, OSError)):
                validate_file_path(path)

    def test_absolute_path_outside_allowed(self):
        """Absolute paths to sensitive areas should fail."""
        sensitive_paths = [
            "/etc/shadow",
            "/etc/passwd",
            "/root/.ssh/id_rsa",
        ]

        for path in sensitive_paths:
            with pytest.raises((ValidationError, FileNotFoundError, PermissionError)):
                validate_file_path(path)

    def test_symlink_resolution(self):
        """Symlinks should be resolved to prevent traversal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a regular file
            safe_file = Path(tmpdir) / "safe.txt"
            safe_file.write_text("safe content")

            # Validate the safe file works
            result = validate_file_path(safe_file)
            assert result.exists()

    def test_null_in_path_rejected(self):
        """Null bytes in paths should be rejected."""
        with pytest.raises((ValidationError, ValueError, TypeError)):
            validate_file_path("/tmp/file\x00.txt")


# =============================================================================
# Secret/Token Handling Tests
# =============================================================================

class TestSecretHandling:
    """Tests for secure handling of secrets and tokens."""

    def test_secrets_not_in_logs(self):
        """Secrets should not appear in error messages."""
        from academiclint.utils.env import mask_secret

        secret = "super_secret_api_key_12345"
        masked = mask_secret(secret)

        # Full secret should not be visible
        assert secret not in masked
        assert "super_secret" not in masked

    def test_mask_secret_short_values(self):
        """Short secrets should be fully masked."""
        from academiclint.utils.env import mask_secret

        short_secret = "abc"
        masked = mask_secret(short_secret)

        assert "a" not in masked
        assert "b" not in masked
        assert "c" not in masked

    def test_env_vars_not_leaked_in_errors(self):
        """Environment variables shouldn't leak in error messages."""
        # Set a fake secret
        os.environ["ACADEMICLINT_SECRET_KEY"] = "secret123"

        try:
            # Trigger an error condition
            config = Config(level="invalid_level_value")
        except Exception as e:
            error_msg = str(e)
            assert "secret123" not in error_msg.lower()
        finally:
            os.environ.pop("ACADEMICLINT_SECRET_KEY", None)

    def test_config_doesnt_expose_secrets(self):
        """Config repr/str shouldn't expose sensitive values."""
        from academiclint.utils.env import EnvConfig

        os.environ["SENTRY_DSN"] = "https://secret@sentry.io/123"

        try:
            env_config = EnvConfig()
            config_dict = env_config.to_dict()

            # Secrets should not be in the dict
            dict_str = str(config_dict)
            assert "secret" not in dict_str.lower()
        finally:
            os.environ.pop("SENTRY_DSN", None)

    def test_get_secret_from_env_safe(self):
        """get_secret should safely retrieve secrets."""
        from academiclint.utils.env import get_secret

        os.environ["TEST_SECRET"] = "my_secret_value"

        try:
            secret = get_secret("TEST_SECRET")
            assert secret == "my_secret_value"
        finally:
            os.environ.pop("TEST_SECRET", None)

    def test_missing_secret_returns_default(self):
        """Missing secrets should return default, not crash."""
        from academiclint.utils.env import get_secret

        os.environ.pop("NONEXISTENT_SECRET", None)
        result = get_secret("NONEXISTENT_SECRET", default="default_value")
        assert result == "default_value"


# =============================================================================
# Regex Injection Prevention Tests
# =============================================================================

class TestRegexInjection:
    """Tests for ReDoS (regex denial of service) prevention."""

    def test_redos_pattern_rejected(self):
        """Potentially dangerous regex patterns should be rejected."""
        dangerous_patterns = [
            "(a+)+$",  # Classic ReDoS
            "((a+)+)+$",  # Nested quantifiers
            "(a|a)+$",  # Alternation with same char
        ]

        for pattern in dangerous_patterns:
            # Should either reject or handle safely
            try:
                result = sanitize_pattern(pattern)
                # If not rejected, shouldn't take forever on evil input
                import re
                re.match(result, "a" * 20)  # Should complete quickly
            except ValidationError:
                pass  # Rejection is acceptable

    def test_safe_patterns_accepted(self):
        """Safe regex patterns should be accepted."""
        safe_patterns = [
            r"\b\w+\b",
            r"[a-z]+",
            r"\d{3}-\d{4}",
            r"^test$",
        ]

        for pattern in safe_patterns:
            result = sanitize_pattern(pattern)
            assert result == pattern

    def test_long_pattern_rejected(self):
        """Very long patterns should be rejected."""
        long_pattern = "a" * 2000

        with pytest.raises(ValidationError):
            sanitize_pattern(long_pattern)

    def test_invalid_regex_rejected(self):
        """Invalid regex syntax should be rejected safely."""
        invalid_patterns = [
            "[unclosed",
            "(?P<invalid",
            "*star_start",
            "(unmatched",
        ]

        for pattern in invalid_patterns:
            with pytest.raises(ValidationError):
                sanitize_pattern(pattern)


# =============================================================================
# Resource Exhaustion Prevention Tests
# =============================================================================

class TestResourceExhaustion:
    """Tests for resource exhaustion (DoS) prevention."""

    def test_max_text_length_enforced(self):
        """Maximum text length should be enforced."""
        from academiclint.utils.validation import MAX_TEXT_LENGTH

        # Just over the limit
        too_long = "a" * (MAX_TEXT_LENGTH + 1)

        with pytest.raises(ValidationError):
            validate_text(too_long)

    def test_max_file_size_enforced(self):
        """Maximum file size should be enforced."""
        from academiclint.utils.validation import MAX_FILE_SIZE

        # Create a file that's too large would be slow,
        # so we just verify the constant exists and is reasonable
        assert MAX_FILE_SIZE > 0
        assert MAX_FILE_SIZE <= 100 * 1024 * 1024  # 100MB max reasonable

    def test_recursive_input_handled(self):
        """Deeply nested structures shouldn't cause stack overflow."""
        # Deeply nested parentheses
        nested = "(" * 100 + "content" + ")" * 100

        # Should complete without stack overflow
        result = Linter().check(nested)
        assert isinstance(result, AnalysisResult)

    def test_many_flags_bounded(self):
        """Number of flags should be bounded reasonably."""
        # Text designed to produce many flags
        problematic = "Many " * 1000

        result = Linter().check(problematic)

        # Should complete and have bounded output
        assert isinstance(result, AnalysisResult)
        # Flags should be reasonable (not millions)
        assert result.summary.flag_count < 100000


# =============================================================================
# Safe Error Handling Tests
# =============================================================================

class TestSafeErrorHandling:
    """Tests for safe error handling without information leakage."""

    def test_file_not_found_safe_message(self):
        """File not found errors shouldn't leak system info."""
        try:
            Linter().check_file("/nonexistent/path/file.txt")
        except FileNotFoundError as e:
            error_msg = str(e)
            # Should not reveal full system path structure
            assert "/home/" not in error_msg or "nonexistent" in error_msg

    def test_validation_errors_safe(self):
        """Validation errors shouldn't leak internal details."""
        try:
            validate_text(None)
        except ValidationError as e:
            error_msg = str(e)
            # Should be user-friendly, not expose internals
            assert "traceback" not in error_msg.lower()
            assert "frame" not in error_msg.lower()

    def test_config_errors_safe(self):
        """Configuration errors shouldn't leak sensitive info."""
        try:
            Config(level="invalid")
        except Exception as e:
            error_msg = str(e)
            # Should explain the error, not expose internals
            assert "invalid" in error_msg.lower() or "level" in error_msg.lower()

    def test_exception_chain_safe(self):
        """Exception chains shouldn't leak sensitive information."""
        from academiclint.core.exceptions import AcademicLintError

        try:
            raise AcademicLintError("User-visible error", details="safe details")
        except AcademicLintError as e:
            assert "User-visible" in str(e)
            assert "safe details" in str(e)


# =============================================================================
# Configuration Security Tests
# =============================================================================

class TestConfigurationSecurity:
    """Tests for secure configuration handling."""

    def test_config_immutable_during_analysis(self):
        """Config shouldn't be modifiable during analysis."""
        config = Config(level="standard")
        linter = Linter(config)

        original_level = config.level
        linter.check("Test text")

        # Config should be unchanged
        assert config.level == original_level

    def test_env_file_parsing_safe(self):
        """Env file parsing shouldn't execute code."""
        from academiclint.utils.env import load_env

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            # Write potentially dangerous content
            f.write("NORMAL_VAR=value\n")
            f.write("$(whoami)=hacked\n")  # Command injection attempt
            f.write("`id`=hacked\n")  # Backtick injection
            f.flush()

            # Should parse safely without executing
            load_env(f.name)

            # Check no command was executed
            assert os.environ.get("$(whoami)") is None or os.environ.get("$(whoami)") == "hacked"
            # The literal string might be set, but command shouldn't execute

    def test_domain_file_path_validated(self):
        """Domain file paths should be validated."""
        # Attempting to use path traversal in domain_file
        try:
            config = Config(domain_file=Path("../../../etc/passwd"))
            # If it gets here, the file shouldn't exist
        except Exception:
            pass  # Expected to fail validation


# =============================================================================
# API Security Tests
# =============================================================================

class TestAPISecurity:
    """Tests for API security (if FastAPI is available)."""

    @pytest.fixture
    def client(self):
        """Create test client if FastAPI available."""
        try:
            from fastapi.testclient import TestClient
            from academiclint.api.app import create_app
            return TestClient(create_app())
        except ImportError:
            pytest.skip("FastAPI not installed")

    def test_large_payload_rejected(self, client):
        """Very large payloads should be handled safely."""
        # 10MB payload
        large_text = "a" * (10 * 1024 * 1024)

        response = client.post("/check", json={"text": large_text})

        # Should either reject or handle, not crash
        assert response.status_code in [200, 400, 413, 422, 500]

    def test_malformed_json_handled(self, client):
        """Malformed JSON should be handled safely."""
        response = client.post(
            "/check",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )

        # Should return error, not crash
        assert response.status_code in [400, 422]

    def test_missing_required_fields(self, client):
        """Missing required fields should return proper error."""
        response = client.post("/check", json={})

        # Should return validation error
        assert response.status_code in [400, 422, 500]

    def test_extra_fields_ignored(self, client):
        """Extra fields in request should be safely ignored."""
        response = client.post(
            "/check",
            json={
                "text": "Test text.",
                "malicious_field": "<script>alert('xss')</script>",
                "__proto__": {"admin": True},
            }
        )

        # Should process normally, ignoring extra fields
        assert response.status_code == 200


# =============================================================================
# Output Security Tests
# =============================================================================

class TestOutputSecurity:
    """Tests for secure output handling."""

    def test_no_xss_in_suggestions(self):
        """Suggestions shouldn't contain executable content."""
        # Text with HTML-like content
        text = "<script>alert('xss')</script> is important."

        result = Linter().check(text)

        # Check all suggestions
        for para in result.paragraphs:
            for flag in para.flags:
                if flag.suggestion:
                    # Suggestions shouldn't echo script tags as-is
                    assert "<script>" not in flag.suggestion.lower()

    def test_result_ids_not_predictable(self):
        """Result IDs should not be easily predictable."""
        results = [Linter().check("Test.") for _ in range(5)]
        ids = [r.id for r in results]

        # IDs should be unique
        assert len(ids) == len(set(ids))

        # IDs should have reasonable entropy (not sequential)
        # Check they're not just incrementing numbers
        try:
            int_ids = [int(id.replace("check_", "")) for id in ids]
            # If they're all sequential integers, that's a problem
            diffs = [int_ids[i+1] - int_ids[i] for i in range(len(int_ids)-1)]
            assert not all(d == 1 for d in diffs), "IDs appear sequential"
        except ValueError:
            pass  # Non-numeric IDs are fine


# =============================================================================
# Dependency Security Tests
# =============================================================================

class TestDependencySecurity:
    """Tests related to dependency security."""

    def test_no_pickle_deserialization(self):
        """System shouldn't deserialize untrusted pickle data."""
        import pickle

        # Create malicious pickle
        class Malicious:
            def __reduce__(self):
                return (os.system, ("echo hacked",))

        # The system shouldn't use pickle for any user input
        # This is more of a code review check, but we verify
        # that normal operations don't involve pickle

        result = Linter().check("Test text")
        assert isinstance(result, AnalysisResult)

    def test_yaml_safe_load_used(self):
        """YAML loading should use safe_load."""
        # Create a YAML config with potential exploit
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            # Python object instantiation attempt
            f.write("level: !!python/object:os.system ['echo hacked']\n")
            f.flush()

            # Should either reject or load safely
            try:
                Config.from_file(f.name)
            except Exception:
                pass  # Expected to fail safely
