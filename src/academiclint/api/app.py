"""FastAPI application for AcademicLint.

This module provides the REST API for semantic clarity analysis.
API documentation is available at /docs (Swagger UI) or /redoc (ReDoc).
"""

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from academiclint import __version__
    from academiclint.api.routes import router

    # API metadata for OpenAPI documentation
    API_TITLE = "AcademicLint API"
    API_DESCRIPTION = """
## Semantic Clarity Analyzer for Academic Writing

AcademicLint analyzes text for semantic clarity issues commonly found in academic writing.
It detects vague language, hedging, circular definitions, and other issues that reduce clarity.

### Features

- **Vagueness Detection**: Identifies imprecise terms like "various", "significant", "generally"
- **Hedge Detection**: Flags excessive hedging like "might", "could possibly", "tends to"
- **Circular Definition Detection**: Catches tautological definitions
- **Citation Needed Detection**: Highlights claims that need supporting evidence
- **Filler Phrase Detection**: Identifies padding that adds no meaning
- **Causal Overreach Detection**: Flags unsupported causal claims
- **Jargon Detection**: Identifies domain-specific terms (configurable)
- **Weasel Word Detection**: Catches vague attributions like "some say", "experts believe"

### Semantic Density Score

Each analysis returns a **density score** (0.0-1.0) indicating the ratio of
meaningful content to filler. Higher scores indicate clearer, more precise writing.

| Grade | Score | Interpretation |
|-------|-------|----------------|
| A | ≥0.8 | Excellent clarity |
| B | ≥0.65 | Good clarity |
| C | ≥0.5 | Acceptable |
| D | ≥0.35 | Needs improvement |
| F | <0.35 | Poor clarity |

### Quick Start

```bash
curl -X POST http://localhost:8080/v1/check \\
  -H "Content-Type: application/json" \\
  -d '{"text": "This is somewhat important."}'
```
"""

    API_TAGS = [
        {
            "name": "Analysis",
            "description": "Text analysis endpoints for semantic clarity checking",
        },
        {
            "name": "Health",
            "description": "Service health and status endpoints",
        },
        {
            "name": "Configuration",
            "description": "Configuration and domain management endpoints",
        },
    ]

    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=__version__,
        openapi_tags=API_TAGS,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        license_info={
            "name": "Polyform Small Business License 1.0.0",
            "url": "https://polyformproject.org/licenses/small-business/1.0.0/",
        },
        contact={
            "name": "AcademicLint Support",
            "email": "support@academiclint.dev",
        },
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router, prefix="/v1")

    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        """Redirect to API documentation."""
        return {
            "message": "AcademicLint API",
            "version": __version__,
            "docs": "/docs",
            "openapi": "/openapi.json",
        }

    # Health check at root level (for load balancers)
    @app.get("/health", include_in_schema=False)
    async def root_health():
        """Root-level health check for load balancers."""
        return {"status": "healthy", "version": __version__}

except ImportError:
    # FastAPI not installed
    app = None
