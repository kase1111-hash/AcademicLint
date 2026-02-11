"""Main CLI entry point for AcademicLint."""

import click

from academiclint import __version__


@click.group()
@click.version_option(version=__version__, prog_name="academiclint")
def cli():
    """AcademicLint - Semantic clarity analyzer for academic writing.

    Grammarly checks your spelling. AcademicLint checks your thinking.
    """
    pass


@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--level",
    type=click.Choice(["relaxed", "standard", "strict", "academic"]),
    default="standard",
    help="Strictness level",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["terminal", "json", "markdown", "github"]),
    default="terminal",
    help="Output format",
)
@click.option("--min-density", type=float, default=0.5, help="Minimum acceptable density")
@click.option("--fail-under", type=float, help="Exit with error if density below threshold")
@click.option("--domain", help="Use built-in domain vocabulary")
@click.option("--domain-file", type=click.Path(exists=True), help="Use custom domain file")
@click.option("--sections", help="Comma-separated sections to analyze")
@click.option("--config", type=click.Path(exists=True), help="Path to config file")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--quiet", is_flag=True, help="Only show summary")
@click.option("--verbose", is_flag=True, help="Show detailed analysis")
@click.option("-o", "--output", type=click.Path(), help="Write output to file")
def check(
    files,
    level,
    output_format,
    min_density,
    fail_under,
    domain,
    domain_file,
    sections,
    config,
    no_color,
    quiet,
    verbose,
    output,
):
    """Analyze text for semantic clarity issues."""
    from academiclint.cli.check import run_check

    run_check(
        files=files,
        level=level,
        output_format=output_format,
        min_density=min_density,
        fail_under=fail_under,
        domain=domain,
        domain_file=domain_file,
        sections=sections,
        config_path=config,
        no_color=no_color,
        quiet=quiet,
        verbose=verbose,
        output_path=output,
    )


@cli.command()
@click.option("--models", help="Specific models to download (comma-separated)")
@click.option("--force", is_flag=True, help="Re-download even if exists")
@click.option("--offline", is_flag=True, help="Configure for offline use only")
def setup(models, force, offline):
    """Download required models."""
    from academiclint.cli.setup import run_setup

    run_setup(models=models, force=force, offline=offline)


if __name__ == "__main__":
    cli()
