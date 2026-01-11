"""Check command implementation for AcademicLint CLI."""

import sys
from pathlib import Path
from typing import Optional

import click


def run_check(
    files: tuple,
    level: str,
    output_format: str,
    min_density: float,
    fail_under: Optional[float],
    domain: Optional[str],
    domain_file: Optional[str],
    sections: Optional[str],
    config_path: Optional[str],
    no_color: bool,
    quiet: bool,
    verbose: bool,
    output_path: Optional[str],
):
    """Run the check command."""
    from academiclint import Config, Linter, OutputConfig
    from academiclint.formatters import get_formatter

    # Build configuration
    if config_path:
        config = Config.from_file(config_path)
    else:
        config = Config()

    # Override with CLI options
    config.level = level
    config.min_density = min_density
    config.fail_under = fail_under
    config.domain = domain

    if domain_file:
        config.domain_file = Path(domain_file)

    if sections:
        config.sections = [s.strip() for s in sections.split(",")]

    config.output = OutputConfig(
        format=output_format,
        color=not no_color,
        show_suggestions=not quiet,
        show_examples=verbose,
    )

    # Initialize linter
    linter = Linter(config)

    # Get formatter
    formatter = get_formatter(output_format, color=not no_color)

    # Process files or stdin
    if not files or files == ("-",):
        # Read from stdin
        text = click.get_text_stream("stdin").read()
        result = linter.check(text)
        output_text = formatter.format(result)
    else:
        # Process files
        results = {}
        for file_path in files:
            path = Path(file_path)
            result = linter.check_file(path)
            results[path] = result

        output_text = formatter.format_multiple(results)

    # Output
    if output_path:
        Path(output_path).write_text(output_text)
        click.echo(f"Output written to {output_path}")
    else:
        click.echo(output_text)

    # Exit code based on fail_under
    if fail_under is not None:
        if files and files != ("-",):
            min_result_density = min(r.density for r in results.values())
        else:
            min_result_density = result.density

        if min_result_density < fail_under:
            sys.exit(2)
