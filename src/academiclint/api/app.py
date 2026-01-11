"""FastAPI application for AcademicLint."""

try:
    from fastapi import FastAPI

    from academiclint import __version__
    from academiclint.api.routes import router

    app = FastAPI(
        title="AcademicLint API",
        description="Semantic clarity analyzer for academic writing",
        version=__version__,
    )

    app.include_router(router, prefix="/v1")

except ImportError:
    # FastAPI not installed
    app = None
