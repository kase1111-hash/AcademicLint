"""Tests for the `academiclint check` command line."""

import json

import pytest
from click.testing import CliRunner

from academiclint.cli.check import EXIT_BELOW_THRESHOLD, EXIT_ERROR
from academiclint.cli.main import cli

VAGUE_TEXT = "Many experts believe that society has changed in significant ways."


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vague_file(tmp_path):
    path = tmp_path / "paper.md"
    path.write_text(VAGUE_TEXT)
    return path


def threshold_suggestion(stdout):
    """Return the 'below threshold' suggestion from JSON output, if any."""
    data = json.loads(stdout)
    result = data[0] if isinstance(data, list) else data
    return next((s for s in result["overall_suggestions"] if "threshold" in s), None)


class TestInput:
    """Tests for where the text to analyze comes from."""

    def test_dash_reads_stdin(self, runner):
        result = runner.invoke(cli, ["check", "-", "--format", "json"], input=VAGUE_TEXT)

        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout)["summary"]["flag_count"] > 0

    def test_directory_expands_to_supported_files(self, runner, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / ".hidden").mkdir()
        (tmp_path / "a.md").write_text(VAGUE_TEXT)
        (tmp_path / "sub" / "b.txt").write_text(VAGUE_TEXT)
        (tmp_path / ".hidden" / "c.md").write_text(VAGUE_TEXT)
        (tmp_path / "script.py").write_text("print('not prose')")

        result = runner.invoke(cli, ["check", str(tmp_path), "--format", "json"])

        assert result.exit_code == 0, result.output
        files = sorted(r["file"] for r in json.loads(result.stdout))
        assert files == [str(tmp_path / "a.md"), str(tmp_path / "sub" / "b.txt")]

    def test_directory_without_supported_files(self, runner, tmp_path):
        result = runner.invoke(cli, ["check", str(tmp_path)])

        assert result.exit_code == EXIT_ERROR
        assert "No supported files" in result.output


class TestConfigPrecedence:
    """Tests for combining --config with command-line options."""

    def test_config_file_values_are_used(self, runner, vague_file, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("min_density: 0.95\n")

        result = runner.invoke(
            cli, ["check", str(vague_file), "--config", str(config), "--format", "json"]
        )

        assert result.exit_code == 0, result.output
        assert "threshold (0.95)" in threshold_suggestion(result.stdout)

    def test_command_line_overrides_config_file(self, runner, vague_file, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("min_density: 0.95\n")

        result = runner.invoke(
            cli,
            ["check", str(vague_file), "--config", str(config), "--min-density", "0.0"],
        )

        assert result.exit_code == 0, result.output
        assert "below threshold" not in result.output

    def test_fail_under_from_config_file(self, runner, vague_file, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("fail_under: 0.99\n")

        result = runner.invoke(cli, ["check", str(vague_file), "--config", str(config)])

        assert result.exit_code == EXIT_BELOW_THRESHOLD


class TestErrors:
    """Expected failures are reported as one-line errors, not tracebacks."""

    @pytest.mark.parametrize(
        ("name", "content", "message"),
        [
            ("paper.docx", "text", "Unsupported file extension"),
            ("empty.md", "", "cannot be empty"),
        ],
    )
    def test_bad_input_file(self, runner, tmp_path, name, content, message):
        path = tmp_path / name
        path.write_text(content)

        result = runner.invoke(cli, ["check", str(path)])

        assert result.exit_code == EXIT_ERROR
        assert message in result.output
        assert "Traceback" not in result.output

    def test_invalid_option_value(self, runner, vague_file):
        result = runner.invoke(cli, ["check", str(vague_file), "--min-density", "5"])

        assert result.exit_code == EXIT_ERROR
        assert "min_density must be between 0.0 and 1.0" in result.output

    def test_unknown_domain(self, runner, vague_file):
        result = runner.invoke(cli, ["check", str(vague_file), "--domain", "medicine"])

        assert result.exit_code == EXIT_ERROR
        assert "Unknown domain 'medicine'" in result.output


class TestOutputOptions:
    """Tests for options that shape the output."""

    def test_quiet_shows_only_summary(self, runner, vague_file):
        result = runner.invoke(cli, ["check", str(vague_file), "--quiet"])

        assert result.exit_code == 0, result.output
        assert "SUMMARY" in result.output
        assert "FLAG:" not in result.output

    def test_sections_warns_unsupported(self, runner, vague_file):
        result = runner.invoke(cli, ["check", str(vague_file), "--sections", "intro"])

        assert result.exit_code == 0, result.output
        assert "--sections is not supported yet" in result.output
