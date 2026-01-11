"""Tests for environment variable and secrets management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from academiclint.utils.env import (
    ENV_PREFIX,
    EnvConfig,
    get_env,
    get_env_bool,
    get_env_float,
    get_env_int,
    get_env_list,
    get_secret,
    load_env,
    mask_secret,
)


class TestLoadEnv:
    """Tests for load_env function."""

    def test_load_existing_env_file(self):
        """Test loading an existing .env file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_VAR=test_value\n")
            f.write("ANOTHER_VAR=another\n")
            f.flush()

            # Clear any existing value
            os.environ.pop("TEST_VAR", None)
            os.environ.pop("ANOTHER_VAR", None)

            result = load_env(f.name)
            assert result is True
            assert os.environ.get("TEST_VAR") == "test_value"
            assert os.environ.get("ANOTHER_VAR") == "another"

            # Cleanup
            os.environ.pop("TEST_VAR", None)
            os.environ.pop("ANOTHER_VAR", None)

    def test_load_nonexistent_file_returns_false(self):
        """Test loading nonexistent file returns False."""
        result = load_env("/nonexistent/.env")
        assert result is False

    def test_does_not_override_by_default(self):
        """Test that existing env vars are not overridden by default."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_OVERRIDE=new_value\n")
            f.flush()

            os.environ["TEST_OVERRIDE"] = "existing_value"
            load_env(f.name, override=False)
            assert os.environ.get("TEST_OVERRIDE") == "existing_value"

            # Cleanup
            os.environ.pop("TEST_OVERRIDE", None)

    def test_override_when_requested(self):
        """Test that env vars are overridden when override=True."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_OVERRIDE2=new_value\n")
            f.flush()

            os.environ["TEST_OVERRIDE2"] = "existing_value"
            load_env(f.name, override=True)
            assert os.environ.get("TEST_OVERRIDE2") == "new_value"

            # Cleanup
            os.environ.pop("TEST_OVERRIDE2", None)

    def test_handles_quoted_values(self):
        """Test that quoted values are unquoted."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write('DOUBLE_QUOTED="double quoted value"\n')
            f.write("SINGLE_QUOTED='single quoted value'\n")
            f.flush()

            os.environ.pop("DOUBLE_QUOTED", None)
            os.environ.pop("SINGLE_QUOTED", None)

            load_env(f.name)
            assert os.environ.get("DOUBLE_QUOTED") == "double quoted value"
            assert os.environ.get("SINGLE_QUOTED") == "single quoted value"

            # Cleanup
            os.environ.pop("DOUBLE_QUOTED", None)
            os.environ.pop("SINGLE_QUOTED", None)

    def test_skips_comments(self):
        """Test that comment lines are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("# This is a comment\n")
            f.write("ACTUAL_VAR=value\n")
            f.write("  # Indented comment\n")
            f.flush()

            os.environ.pop("ACTUAL_VAR", None)
            load_env(f.name)
            assert os.environ.get("ACTUAL_VAR") == "value"

            # Cleanup
            os.environ.pop("ACTUAL_VAR", None)

    def test_skips_empty_lines(self):
        """Test that empty lines are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("\n")
            f.write("VAR_AFTER_EMPTY=value\n")
            f.write("\n\n")
            f.flush()

            os.environ.pop("VAR_AFTER_EMPTY", None)
            load_env(f.name)
            assert os.environ.get("VAR_AFTER_EMPTY") == "value"

            # Cleanup
            os.environ.pop("VAR_AFTER_EMPTY", None)


class TestGetEnv:
    """Tests for get_env function."""

    def test_get_existing_var(self):
        """Test getting an existing environment variable."""
        os.environ["ACADEMICLINT_TEST_VAR"] = "test_value"
        result = get_env("TEST_VAR")
        assert result == "test_value"
        os.environ.pop("ACADEMICLINT_TEST_VAR", None)

    def test_get_with_default(self):
        """Test getting nonexistent var with default."""
        os.environ.pop("ACADEMICLINT_NONEXISTENT", None)
        result = get_env("NONEXISTENT", default="default_value")
        assert result == "default_value"

    def test_get_required_missing(self):
        """Test that required=True raises error for missing var."""
        os.environ.pop("ACADEMICLINT_REQUIRED_VAR", None)
        with pytest.raises(ValueError, match="Required environment variable"):
            get_env("REQUIRED_VAR", required=True)

    def test_get_without_prefix(self):
        """Test getting var without prefix."""
        os.environ["CUSTOM_VAR"] = "custom_value"
        result = get_env("CUSTOM_VAR", prefix=False)
        assert result == "custom_value"
        os.environ.pop("CUSTOM_VAR", None)

    def test_prefix_is_added(self):
        """Test that prefix is added by default."""
        os.environ["ACADEMICLINT_PREFIXED"] = "prefixed_value"
        result = get_env("PREFIXED")
        assert result == "prefixed_value"
        os.environ.pop("ACADEMICLINT_PREFIXED", None)


class TestGetEnvBool:
    """Tests for get_env_bool function."""

    @pytest.mark.parametrize("value,expected", [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("Yes", True),
        ("on", True),
        ("ON", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("no", False),
        ("off", False),
        ("", False),
        ("invalid", False),
    ])
    def test_bool_parsing(self, value, expected):
        """Test boolean parsing for various values."""
        os.environ["ACADEMICLINT_BOOL_TEST"] = value
        result = get_env_bool("BOOL_TEST")
        assert result == expected
        os.environ.pop("ACADEMICLINT_BOOL_TEST", None)

    def test_default_when_missing(self):
        """Test default value when var is missing."""
        os.environ.pop("ACADEMICLINT_MISSING_BOOL", None)
        assert get_env_bool("MISSING_BOOL", default=True) is True
        assert get_env_bool("MISSING_BOOL", default=False) is False


class TestGetEnvInt:
    """Tests for get_env_int function."""

    def test_valid_int(self):
        """Test parsing valid integer."""
        os.environ["ACADEMICLINT_INT_VAR"] = "42"
        result = get_env_int("INT_VAR")
        assert result == 42
        os.environ.pop("ACADEMICLINT_INT_VAR", None)

    def test_negative_int(self):
        """Test parsing negative integer."""
        os.environ["ACADEMICLINT_NEG_INT"] = "-10"
        result = get_env_int("NEG_INT")
        assert result == -10
        os.environ.pop("ACADEMICLINT_NEG_INT", None)

    def test_invalid_int_returns_default(self):
        """Test that invalid integer returns default."""
        os.environ["ACADEMICLINT_INVALID_INT"] = "not_a_number"
        result = get_env_int("INVALID_INT", default=100)
        assert result == 100
        os.environ.pop("ACADEMICLINT_INVALID_INT", None)

    def test_default_when_missing(self):
        """Test default when var is missing."""
        os.environ.pop("ACADEMICLINT_MISSING_INT", None)
        result = get_env_int("MISSING_INT", default=99)
        assert result == 99


class TestGetEnvFloat:
    """Tests for get_env_float function."""

    def test_valid_float(self):
        """Test parsing valid float."""
        os.environ["ACADEMICLINT_FLOAT_VAR"] = "3.14"
        result = get_env_float("FLOAT_VAR")
        assert result == 3.14
        os.environ.pop("ACADEMICLINT_FLOAT_VAR", None)

    def test_integer_as_float(self):
        """Test parsing integer as float."""
        os.environ["ACADEMICLINT_INT_AS_FLOAT"] = "42"
        result = get_env_float("INT_AS_FLOAT")
        assert result == 42.0
        os.environ.pop("ACADEMICLINT_INT_AS_FLOAT", None)

    def test_invalid_float_returns_default(self):
        """Test that invalid float returns default."""
        os.environ["ACADEMICLINT_INVALID_FLOAT"] = "not_a_number"
        result = get_env_float("INVALID_FLOAT", default=1.5)
        assert result == 1.5
        os.environ.pop("ACADEMICLINT_INVALID_FLOAT", None)


class TestGetEnvList:
    """Tests for get_env_list function."""

    def test_comma_separated(self):
        """Test parsing comma-separated list."""
        os.environ["ACADEMICLINT_LIST_VAR"] = "a,b,c"
        result = get_env_list("LIST_VAR")
        assert result == ["a", "b", "c"]
        os.environ.pop("ACADEMICLINT_LIST_VAR", None)

    def test_custom_separator(self):
        """Test parsing with custom separator."""
        os.environ["ACADEMICLINT_CUSTOM_SEP"] = "a;b;c"
        result = get_env_list("CUSTOM_SEP", separator=";")
        assert result == ["a", "b", "c"]
        os.environ.pop("ACADEMICLINT_CUSTOM_SEP", None)

    def test_strips_whitespace(self):
        """Test that whitespace is stripped."""
        os.environ["ACADEMICLINT_WHITESPACE"] = "  a , b , c  "
        result = get_env_list("WHITESPACE")
        assert result == ["a", "b", "c"]
        os.environ.pop("ACADEMICLINT_WHITESPACE", None)

    def test_skips_empty_items(self):
        """Test that empty items are skipped."""
        os.environ["ACADEMICLINT_EMPTY_ITEMS"] = "a,,b,  ,c"
        result = get_env_list("EMPTY_ITEMS")
        assert result == ["a", "b", "c"]
        os.environ.pop("ACADEMICLINT_EMPTY_ITEMS", None)

    def test_default_when_missing(self):
        """Test default when var is missing."""
        os.environ.pop("ACADEMICLINT_MISSING_LIST", None)
        result = get_env_list("MISSING_LIST", default=["x", "y"])
        assert result == ["x", "y"]

    def test_empty_default(self):
        """Test empty default when var is missing."""
        os.environ.pop("ACADEMICLINT_EMPTY_DEFAULT", None)
        result = get_env_list("EMPTY_DEFAULT")
        assert result == []


class TestGetSecret:
    """Tests for get_secret function."""

    def test_get_from_env(self):
        """Test getting secret from environment."""
        os.environ["MY_SECRET"] = "secret_value"
        result = get_secret("MY_SECRET")
        assert result == "secret_value"
        os.environ.pop("MY_SECRET", None)

    def test_default_when_missing(self):
        """Test default when secret is missing."""
        os.environ.pop("MISSING_SECRET", None)
        result = get_secret("MISSING_SECRET", default="default_secret")
        assert result == "default_secret"

    def test_secrets_manager_called(self):
        """Test that secrets manager is called when env var missing."""
        os.environ.pop("MANAGED_SECRET", None)
        manager = MagicMock(return_value="managed_value")

        result = get_secret("MANAGED_SECRET", secrets_manager=manager)
        assert result == "managed_value"
        manager.assert_called_once_with("MANAGED_SECRET")

    def test_env_takes_precedence_over_manager(self):
        """Test that env var takes precedence over secrets manager."""
        os.environ["PRECEDENCE_SECRET"] = "env_value"
        manager = MagicMock(return_value="managed_value")

        result = get_secret("PRECEDENCE_SECRET", secrets_manager=manager)
        assert result == "env_value"
        manager.assert_not_called()

        os.environ.pop("PRECEDENCE_SECRET", None)

    def test_manager_exception_falls_back_to_default(self):
        """Test that manager exception falls back to default."""
        os.environ.pop("FAILING_SECRET", None)
        manager = MagicMock(side_effect=Exception("Manager failed"))

        result = get_secret("FAILING_SECRET", default="fallback", secrets_manager=manager)
        assert result == "fallback"


class TestMaskSecret:
    """Tests for mask_secret function."""

    def test_mask_long_secret(self):
        """Test masking a long secret."""
        result = mask_secret("mysecretpassword")
        assert result == "************word"
        assert "password" not in result

    def test_mask_short_secret(self):
        """Test masking a short secret."""
        result = mask_secret("abc")
        assert result == "***"
        assert "a" not in result
        assert "b" not in result
        assert "c" not in result

    def test_custom_visible_chars(self):
        """Test custom number of visible characters."""
        result = mask_secret("mysecretpassword", visible_chars=6)
        assert result == "**********ssword"

    def test_zero_visible_chars(self):
        """Test with zero visible characters."""
        result = mask_secret("secret", visible_chars=0)
        assert result == "******"

    def test_visible_chars_equals_length(self):
        """Test when visible_chars equals secret length."""
        result = mask_secret("test", visible_chars=4)
        assert result == "test"


class TestEnvConfig:
    """Tests for EnvConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        # Clear any env vars that might affect defaults
        for var in ["LEVEL", "MIN_DENSITY", "OUTPUT_FORMAT", "COLOR", "LOG_LEVEL",
                    "API_HOST", "API_PORT", "WORKERS"]:
            os.environ.pop(f"ACADEMICLINT_{var}", None)
        os.environ.pop("SENTRY_DSN", None)

        config = EnvConfig()
        assert config.level == "standard"
        assert config.min_density == 0.50
        assert config.output_format == "terminal"
        assert config.color is True

    def test_custom_level(self):
        """Test custom level from environment."""
        os.environ["ACADEMICLINT_LEVEL"] = "strict"
        config = EnvConfig()
        assert config.level == "strict"
        os.environ.pop("ACADEMICLINT_LEVEL", None)

    def test_custom_min_density(self):
        """Test custom min_density from environment."""
        os.environ["ACADEMICLINT_MIN_DENSITY"] = "0.75"
        config = EnvConfig()
        assert config.min_density == 0.75
        os.environ.pop("ACADEMICLINT_MIN_DENSITY", None)

    def test_to_dict(self):
        """Test to_dict method."""
        for var in ["LEVEL", "MIN_DENSITY", "OUTPUT_FORMAT", "COLOR", "LOG_LEVEL",
                    "API_HOST", "API_PORT", "WORKERS", "DOMAIN", "FAIL_UNDER"]:
            os.environ.pop(f"ACADEMICLINT_{var}", None)

        config = EnvConfig()
        d = config.to_dict()

        assert "level" in d
        assert "min_density" in d
        assert "output_format" in d
        # Secrets should not be in dict
        assert "sentry_dsn" not in d


class TestEnvPrefix:
    """Tests for ENV_PREFIX constant."""

    def test_prefix_value(self):
        """Test that prefix is correct."""
        assert ENV_PREFIX == "ACADEMICLINT_"
