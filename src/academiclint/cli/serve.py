"""Serve command implementation for AcademicLint CLI."""

import click


def run_serve(host: str, port: int, reload: bool, workers: int):
    """Run the REST API server."""
    try:
        import uvicorn
    except ImportError:
        click.echo("Error: uvicorn not installed. Install with: pip install academiclint[api]", err=True)
        return

    click.echo(f"Starting AcademicLint API server on {host}:{port}")

    uvicorn.run(
        "academiclint.api.app:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
    )
