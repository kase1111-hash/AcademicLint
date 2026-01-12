"""FastAPI application for AcademicLint."""

try:
    from fastapi import FastAPI
    from fastapi.openapi.utils import get_openapi

    from academiclint import __version__
    from academiclint.api.routes import router

    DESCRIPTION = """
## AcademicLint API

A semantic clarity analyzer for academic writing that detects common issues
in scholarly prose and provides actionable suggestions for improvement.

### Features

- **Semantic Density Analysis**: Measures the ratio of meaningful content to filler
- **Eight Detection Types**: Identifies vagueness, unsupported causation, circular definitions, weasel words, hedge stacking, jargon density, missing citations, and filler phrases
- **Domain-Aware Analysis**: Customize detection with academic domain vocabularies
- **Multiple Strictness Levels**: From relaxed to academic-grade strictness

### Quick Start

```python
import requests

response = requests.post(
    "http://localhost:8080/v1/check",
    json={"text": "Your academic text here..."}
)
print(response.json()["summary"]["density_grade"])
```

### Authentication

Currently, the API does not require authentication. For production deployments,
consider adding API key authentication via a reverse proxy.

### Rate Limiting

No rate limiting is enforced by default. Configure rate limiting at the
infrastructure level for production use.
"""

    TAGS_METADATA = [
        {
            "name": "analysis",
            "description": "Text analysis endpoints for checking semantic clarity",
        },
        {
            "name": "domains",
            "description": "Domain vocabulary management and listing",
        },
        {
            "name": "health",
            "description": "Health check and status endpoints",
        },
    ]

    app = FastAPI(
        title="AcademicLint API",
        description=DESCRIPTION,
        version=__version__,
        openapi_tags=TAGS_METADATA,
        contact={
            "name": "AcademicLint Support",
            "url": "https://github.com/academiclint/academiclint",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_url="/v1/openapi.json",
        docs_url="/v1/docs",
        redoc_url="/v1/redoc",
    )

    app.include_router(router, prefix="/v1")

    def custom_openapi():
        """Generate custom OpenAPI schema with additional metadata."""
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=TAGS_METADATA,
        )
        openapi_schema["info"]["x-logo"] = {
            "url": "https://raw.githubusercontent.com/academiclint/academiclint/main/docs/logo.png"
        }
        # Add server information
        openapi_schema["servers"] = [
            {"url": "http://localhost:8080", "description": "Local development server"},
            {"url": "https://api.academiclint.io", "description": "Production server"},
        ]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

except ImportError:
    # FastAPI not installed
    app = None
