"""Setup command implementation for AcademicLint CLI."""

import subprocess
from typing import Optional

import click

from academiclint.models.manager import MODEL_DOWNLOAD_TIMEOUT, ModelManager


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

    # Validate and download spaCy models
    for model in model_list:
        try:
            ModelManager.validate_model_name(model)
        except ValueError as e:
            click.echo(f"  Skipping invalid model name: {e}", err=True)
            continue
        download_spacy_model(model, force=force)

    click.echo("\nSetup complete!")
    click.echo("Run 'academiclint check <file>' to analyze your writing.")


def download_spacy_model(model: str, force: bool = False):
    """Download a spaCy model."""
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
            timeout=MODEL_DOWNLOAD_TIMEOUT,
        )

        if result.returncode == 0:
            click.echo(f"  Successfully downloaded {model}")
        else:
            click.echo(f"  Error downloading {model}: {result.stderr}", err=True)

    except subprocess.TimeoutExpired:
        click.echo(f"  Error: Download of {model} timed out", err=True)
    except Exception as e:
        click.echo(f"  Error: {e}", err=True)
