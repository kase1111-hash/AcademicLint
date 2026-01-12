# =============================================================================
# AcademicLint Docker Image
# =============================================================================
# Multi-stage build for optimized production image
#
# Build targets:
#   production  - Minimal runtime image (default)
#   development - Full dev environment with tests
#   api         - API server optimized
#
# Build commands:
#   docker build -t academiclint .
#   docker build -t academiclint:dev --target development .
#   docker build -t academiclint:api --target api .
#
# Run examples:
#   docker run -it academiclint --help
#   docker run -it academiclint analyze "Your text here"
#   docker run -p 8080:8080 academiclint:api
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and download models
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependency files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install package and dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir build wheel && \
    pip install --no-cache-dir -e ".[api]"

# Download spaCy model (use smaller model for container size)
RUN python -m spacy download en_core_web_sm

# Build wheel for distribution
RUN python -m build --wheel

# -----------------------------------------------------------------------------
# Stage 2: Production - Minimal runtime image
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

LABEL maintainer="AcademicLint Team"
LABEL description="Semantic clarity analyzer for academic writing"
LABEL version="0.1.0"
LABEL org.opencontainers.image.source="https://github.com/academiclint/academiclint"

WORKDIR /app

# Create non-root user for security
RUN groupadd -r academiclint && \
    useradd -r -g academiclint academiclint

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code and config
COPY --from=builder /build/src/ ./src/
COPY --from=builder /build/pyproject.toml ./
COPY config/ ./config/

# Install the package
RUN pip install --no-cache-dir -e .

# Create directories for runtime data
RUN mkdir -p /app/logs /app/cache && \
    chown -R academiclint:academiclint /app

# Switch to non-root user
USER academiclint

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ACADEMICLINT_ENV=production \
    ACADEMICLINT_LEVEL=standard

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import academiclint; print('healthy')" || exit 1

# Default entrypoint
ENTRYPOINT ["python", "-m", "academiclint"]
CMD ["--help"]

# -----------------------------------------------------------------------------
# Stage 3: API Server - Optimized for serving
# -----------------------------------------------------------------------------
FROM production AS api

ENV ACADEMICLINT_API_HOST=0.0.0.0 \
    ACADEMICLINT_API_PORT=8080

# Override health check for API
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["serve", "--host", "0.0.0.0", "--port", "8080"]

# -----------------------------------------------------------------------------
# Stage 4: Development - Full development environment
# -----------------------------------------------------------------------------
FROM production AS development

USER root

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-asyncio \
    httpx \
    ruff \
    mypy \
    bandit

# Copy test files
COPY tests/ ./tests/

# Set ownership
RUN chown -R academiclint:academiclint /app

# Switch back to non-root user
USER academiclint

ENV ACADEMICLINT_ENV=development

# Override command for development
CMD ["--help"]
