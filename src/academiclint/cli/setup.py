"""Setup command implementation for AcademicLint CLI."""

from typing import Optional

import click


def run_setup(models: Optional[str], force: bool, offline: bool):
    """Run the setup command to download models."""
    click.echo("Setting up AcademicLint...")

    if offline:
        click.echo("Configuring for offline use...")
        click.echo("Note: You'll need to manually install spaCy models.")
        return

    # Determine which models to download
    if models:
        model_list = [m.strip() for m in models.split(",")]
    else:
        model_list = ["en_core_web_lg"]

    # Download spaCy models
    for model in model_list:
        if model.startswith("en_core_web"):
            download_spacy_model(model, force=force)

    click.echo("\nSetup complete!")
    click.echo("Run 'academiclint check <file>' to analyze your writing.")


def download_spacy_model(model: str, force: bool = False):
    """Download a spaCy model."""
    import subprocess

    click.echo(f"Downloading spaCy model: {model}")

    try:
        # Check if already installed
        if not force:
            try:
                import spacy

                spacy.load(model)
                click.echo(f"  Model {model} already installed. Use --force to re-download.")
                return
            except OSError:
                pass

        # Download the model
        result = subprocess.run(
            ["python", "-m", "spacy", "download", model],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            click.echo(f"  Successfully downloaded {model}")
        else:
            click.echo(f"  Error downloading {model}: {result.stderr}", err=True)

    except Exception as e:
        click.echo(f"  Error: {e}", err=True)
