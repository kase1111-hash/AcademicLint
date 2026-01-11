# AcademicLint Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Stage 1: Builder - Install dependencies and download models
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_lg

# =============================================================================
# Stage 2: Production - Minimal runtime image
# =============================================================================
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user for security
RUN groupadd -r academiclint && \
    useradd -r -g academiclint academiclint

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src/ ./src/
COPY pyproject.toml .

# Install the package
RUN pip install --no-cache-dir -e .

# Set ownership
RUN chown -R academiclint:academiclint /app

# Switch to non-root user
USER academiclint

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ACADEMICLINT_LEVEL=standard

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import academiclint; print('healthy')" || exit 1

# Default command: Start API server
CMD ["python", "-m", "academiclint.cli.main", "serve", "--host", "0.0.0.0", "--port", "8080"]

# =============================================================================
# Stage 3: Development - Full development environment
# =============================================================================
FROM production as development

USER root

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy test files
COPY tests/ ./tests/

# Switch back to non-root user
USER academiclint

# Override command for development
CMD ["pytest", "--cov=academiclint", "-v"]
