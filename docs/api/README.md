# AcademicLint API Documentation

## Overview

The AcademicLint API provides programmatic access to semantic clarity analysis for academic writing.

## Base URL

```
http://localhost:8080
```

## Interactive Documentation

When the API is running, interactive documentation is available at:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## Quick Start

### Start the API Server

```bash
# Using Docker
docker-compose up api

# Using Make
make dev-server

# Directly
uvicorn academiclint.api.app:app --host 0.0.0.0 --port 8080
```

### Analyze Text

```bash
curl -X POST http://localhost:8080/v1/check \
  -H "Content-Type: application/json" \
  -d '{"text": "This is somewhat important for various reasons."}'
```

## Endpoints

### POST /v1/check

Analyze text for semantic clarity issues.

**Request Body:**
```json
{
  "text": "Your text to analyze",
  "config": {
    "level": "standard",
    "min_density": 0.5,
    "domain": "computer_science",
    "domain_terms": ["custom", "terms"]
  }
}
```

**Configuration Options:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | string | `"standard"` | Analysis strictness: `relaxed`, `standard`, `strict`, `academic` |
| `min_density` | float | `0.5` | Minimum acceptable density score (0.0-1.0) |
| `domain` | string | `null` | Built-in domain name for specialized terminology |
| `domain_terms` | array | `null` | Custom terms to exclude from jargon detection |

**Response:**
```json
{
  "id": "analysis-uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "input_length": 47,
  "processing_time_ms": 150,
  "summary": {
    "density": 0.65,
    "density_grade": "B",
    "flag_count": 2,
    "word_count": 100,
    "sentence_count": 5,
    "paragraph_count": 1,
    "concept_count": 15,
    "filler_ratio": 0.15,
    "suggestion_count": 2
  },
  "paragraphs": [...],
  "overall_suggestions": [...]
}
```

### GET /v1/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "models_loaded": true
}
```

### GET /v1/domains

List available built-in domains.

**Response:**
```json
{
  "domains": ["physics", "biology", "computer_science", ...]
}
```

## Flag Types

The analysis detects the following issue types:

| Type | Description | Example |
|------|-------------|---------|
| `vague` | Imprecise language | "various", "significant" |
| `hedge` | Hedging language | "somewhat", "might" |
| `circular` | Tautological definitions | "X is defined as X" |
| `citation_needed` | Claims needing evidence | "Studies show..." |
| `filler` | Empty phrases | "It is important to note that" |
| `causal` | Unsupported causation | "This causes..." |
| `jargon` | Domain-specific terms | Technical terminology |
| `weasel` | Vague attribution | "Some experts believe" |

## Severity Levels

| Level | Description |
|-------|-------------|
| `low` | Minor suggestion, optional fix |
| `medium` | Recommended improvement |
| `high` | Important issue to address |
| `critical` | Significantly impacts clarity |

## Density Grades

| Grade | Score Range | Interpretation |
|-------|-------------|----------------|
| A | ≥ 0.80 | Excellent clarity |
| B | 0.65 - 0.79 | Good clarity |
| C | 0.50 - 0.64 | Acceptable |
| D | 0.35 - 0.49 | Needs improvement |
| F | < 0.35 | Poor clarity |

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Text cannot be empty"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message describing the issue"
}
```

## Postman Collection

A Postman collection is available for testing:

```
docs/api/postman_collection.json
```

Import this file into Postman to get pre-configured requests for all endpoints.

## Rate Limiting

The default configuration does not include rate limiting. For production deployments, configure rate limiting at the reverse proxy or load balancer level.

## CORS

CORS is enabled by default for development. Configure `allow_origins` in production to restrict allowed origins.
