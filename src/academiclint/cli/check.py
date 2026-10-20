"""Check command implementation for AcademicLint CLI."""

import dataclasses
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

from academiclint.core.exceptions import (
    AcademicLintError,
    EmptyTextError,
    ParsingError,
    ValidationError,
)
from academiclint.utils.validation import SUPPORTED_EXTENSIONS

if TYPE_CHECKING:
    from academiclint import Linter
    from academiclint.core.result import AnalysisResult

# Exit codes
EXIT_ERROR = 1  # Analysis could not run (bad input, config, or missing model)
EXIT_BELOW_THRESHOLD = 2  # A document's density is below --fail-under


def run_check(
    files: tuple,
    level: str | None,
    output_format: str | None,
    min_density: float | None,
    fail_under: float | None,
    domain: str | None,
    domain_file: str | None,
    sections: str | None,
    config_path: str | None,
    no_color: bool,
    quiet: bool,
    verbose: bool,
    output_path: str | None,
):
    """Run the check command, reporting expected failures without a traceback."""
    try:
        _run_check(
            files=files,
            level=level,
            output_format=output_format,
            min_density=min_density,
            fail_under=fail_under,
            domain=domain,
            domain_file=domain_file,
            sections=sections,
            config_path=config_path,
            no_color=no_color,
            quiet=quiet,
            output_path=output_path,
        )
    except BrokenPipeError:
        raise  # Output piped into e.g. `head`; click exits quietly
    except (AcademicLintError, OSError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(EXIT_ERROR)


def _run_check(
    files: tuple,
    level: str | None,
    output_format: str | None,
    min_density: float | None,
    fail_under: float | None,
    domain: str | None,
    domain_file: str | None,
    sections: str | None,
    config_path: str | None,
    no_color: bool,
    quiet: bool,
    output_path: str | None,
):
    from academiclint import Config, Linter
    from academiclint.formatters import get_formatter

    # Build configuration
    config = Config.from_file(config_path) if config_path else Config()

    # Command-line options override the config file only when given;
    # dataclasses.replace re-runs Config validation on the result
    overrides: dict[str, Any] = {
        "level": level,
        "min_density": min_density,
        "fail_under": fail_under,
        "domain": domain,
        "domain_file": Path(domain_file) if domain_file else None,
    }
    config = dataclasses.replace(
        config, **{name: value for name, value in overrides.items() if value is not None}
    )

    if sections or config.sections:
        click.echo(
            "Warning: section filtering is not supported yet; analyzing whole documents",
            err=True,
        )

    # Initialize linter
    linter = Linter(config)

    # Get formatter
    formatter = get_formatter(
        output_format or config.output.format,
        color=config.output.color and not no_color,
        quiet=quiet,
        min_density=config.min_density,
    )

    if "-" in files and len(files) > 1:
        raise click.UsageError("'-' (stdin) cannot be combined with other paths")

    # Process files or stdin
    failed = 0
    if not files or files == ("-",):
        # Read from stdin
        result = linter.check(sys.stdin.read())
        output_text = formatter.format(result)
        densities = [result.density]
    else:
        results, failed = _check_files(linter, files)
        output_text = formatter.format_multiple(results)
        densities = [r.density for r in results.values()]

    # Output
    if output_path:
        Path(output_path).write_text(output_text, encoding="utf-8")
        click.echo(f"Output written to {output_path}")
    else:
        click.echo(output_text)

    if failed:
        sys.exit(EXIT_ERROR)

    # Exit code based on fail_under
    if config.fail_under is not None and min(densities) < config.fail_under:
        sys.exit(EXIT_BELOW_THRESHOLD)


def _check_files(linter: "Linter", files: tuple) -> tuple[dict[Path, "AnalysisResult"], int]:
    """Analyze each file, reporting failures without stopping the rest.

    Returns:
        Results for the files analyzed, and the number of files that failed

    Raises:
        EmptyTextError: If every file was skipped for having no text
    """
    results = {}
    failed = 0
    for path, from_directory in _expand_paths(files):
        try:
            results[path] = linter.check_file(path)
        except EmptyTextError as e:
            if from_directory:
                # e.g. a LaTeX main file holding only \input commands
                click.echo(f"Warning: skipping {path}: {e}", err=True)
            else:
                click.echo(f"Error: {path}: {e}", err=True)
                failed += 1
        except (ValidationError, ParsingError, OSError) as e:
            click.echo(f"Error: {path}: {e}", err=True)
            failed += 1

    if not results:
        if failed:
            sys.exit(EXIT_ERROR)
        raise EmptyTextError("None of the files contain text to analyze")
    return results, failed


def _expand_paths(files: tuple) -> list[tuple[Path, bool]]:
    """Expand directories into the supported files they contain.

    Returns:
        (path, came_from_a_directory) pairs

    Raises:
        ValidationError: If a directory contains no supported files
    """
    paths = []
    for name in files:
        path = Path(name)
        if not path.is_dir():
            paths.append((path, False))
            continue

        found = sorted(
            p
            for p in path.rglob("*")
            if p.is_file()
            and p.suffix.lower() in SUPPORTED_EXTENSIONS
            # Skip hidden directories such as .git
            and not any(part.startswith(".") for part in p.relative_to(path).parts)
        )
        if not found:
            raise ValidationError(
                f"No supported files in directory '{path}' "
                f"(looked for {', '.join(sorted(SUPPORTED_EXTENSIONS))})"
            )
        paths.extend((p, True) for p in found)
    return paths
