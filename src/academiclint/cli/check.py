"""Check command implementation for AcademicLint CLI."""

import dataclasses
import sys
from pathlib import Path
from typing import Any

import click

from academiclint.core.exceptions import AcademicLintError, ValidationError
from academiclint.utils.validation import SUPPORTED_EXTENSIONS

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

    if sections:
        click.echo("Warning: --sections is not supported yet; analyzing whole documents", err=True)

    # Initialize linter
    linter = Linter(config)

    # Get formatter
    formatter = get_formatter(
        output_format or config.output.format,
        color=config.output.color and not no_color,
        quiet=quiet,
        min_density=config.min_density,
    )

    # Process files or stdin
    if not files or files == ("-",):
        # Read from stdin
        result = linter.check(sys.stdin.read())
        output_text = formatter.format(result)
        densities = [result.density]
    else:
        # Process files
        results = {path: linter.check_file(path) for path in _expand_paths(files)}
        output_text = formatter.format_multiple(results)
        densities = [r.density for r in results.values()]

    # Output
    if output_path:
        Path(output_path).write_text(output_text)
        click.echo(f"Output written to {output_path}")
    else:
        click.echo(output_text)

    # Exit code based on fail_under
    if config.fail_under is not None and min(densities) < config.fail_under:
        sys.exit(EXIT_BELOW_THRESHOLD)


def _expand_paths(files: tuple) -> list[Path]:
    """Expand directories into the supported files they contain.

    Raises:
        ValidationError: If a directory contains no supported files
    """
    paths = []
    for name in files:
        path = Path(name)
        if not path.is_dir():
            paths.append(path)
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
        paths.extend(found)
    return paths
