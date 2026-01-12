# API Reference

## Interactive API Documentation

AcademicLint provides interactive API documentation via Swagger UI and ReDoc when the server is running:

- **Swagger UI**: `http://localhost:8080/v1/docs` - Interactive API explorer
- **ReDoc**: `http://localhost:8080/v1/redoc` - Beautiful API documentation
- **OpenAPI JSON**: `http://localhost:8080/v1/openapi.json` - Raw OpenAPI schema

### Additional Resources

- [OpenAPI Specification](./openapi.yaml) - Complete OpenAPI 3.1.0 specification
- [Postman Collection](./postman_collection.json) - Import into Postman for easy testing

## Python Library

### Linter

The main class for analyzing text.

```python
from academiclint import Linter, Config

# Initialize with default config
linter = Linter()

# Initialize with custom config
config = Config(level="strict", min_density=0.6)
linter = Linter(config)
```

#### Methods

##### `check(text: str) -> AnalysisResult`

Analyze text for semantic clarity issues.

```python
result = linter.check("Your text here...")
```

##### `check_file(path: Path) -> AnalysisResult`

Analyze a file.

```python
from pathlib import Path
result = linter.check_file(Path("paper.md"))
```

##### `check_files(paths: list[Path]) -> dict[Path, AnalysisResult]`

Analyze multiple files.

```python
results = linter.check_files([Path("ch1.md"), Path("ch2.md")])
```

##### `check_stream(text: str) -> Iterator[ParagraphResult]`

Stream analysis paragraph by paragraph.

```python
for para in linter.check_stream(text):
    print(f"Paragraph {para.index}: {para.density}")
```

### AnalysisResult

Complete analysis result for a document.

```python
result = linter.check(text)

# Access overall density
print(result.density)

# Access summary statistics
print(result.summary.density_grade)
print(result.summary.flag_count)
print(result.summary.word_count)

# Iterate over flags
for flag in result.flags:
    print(f"{flag.type.value}: {flag.term}")
    print(f"  {flag.message}")
    print(f"  Suggestion: {flag.suggestion}")

# Iterate over paragraphs
for para in result.paragraphs:
    print(f"Paragraph {para.index}: density={para.density}")
```

### Flag

A single issue detected in the text.

```python
flag.type        # FlagType enum
flag.term        # The flagged text
flag.span        # Span with start/end positions
flag.line        # Line number (1-indexed)
flag.column      # Column number (1-indexed)
flag.severity    # Severity enum (LOW, MEDIUM, HIGH)
flag.message     # Human-readable explanation
flag.suggestion  # How to fix it
flag.context     # Surrounding text
```

### FlagType

```python
from academiclint import FlagType

FlagType.UNDERSPECIFIED    # Vague terms
FlagType.UNSUPPORTED_CAUSAL  # Causal claims without evidence
FlagType.CIRCULAR          # Circular definitions
FlagType.WEASEL            # Vague attribution
FlagType.HEDGE_STACK       # Excessive hedging
FlagType.JARGON_DENSE      # Unexplained jargon
FlagType.CITATION_NEEDED   # Missing citations
FlagType.FILLER            # Empty phrases
```

## REST API

### Endpoints

#### POST /v1/check

Analyze text for semantic clarity issues.

**Request:**

```json
{
  "text": "Your academic text here...",
  "config": {
    "level": "standard",
    "min_density": 0.5,
    "domain": "philosophy",
    "domain_terms": ["additional", "terms"]
  }
}
```

**Response:**

```json
{
  "id": "check_abc123",
  "created_at": "2025-01-11T10:30:00Z",
  "input_length": 1547,
  "processing_time_ms": 234,
  "summary": {
    "density": 0.43,
    "density_grade": "thin",
    "flag_count": 12,
    "word_count": 287
  },
  "paragraphs": [...],
  "overall_suggestions": [...]
}
```

#### GET /v1/health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "models_loaded": true
}
```

#### GET /v1/domains

List available domains.

**Response:**

```json
{
  "domains": [
    {"name": "philosophy", "term_count": 50},
    {"name": "computer-science", "term_count": 80}
  ]
}
```

### Starting the Server

```bash
# Start local server
academiclint serve --port 8080

# With auto-reload for development
academiclint serve --reload

# With multiple workers
academiclint serve --workers 4
```

### Using the API

```python
import requests

response = requests.post(
    "http://localhost:8080/v1/check",
    json={
        "text": "Your text here...",
        "config": {"level": "standard"}
    }
)

result = response.json()
print(f"Density: {result['summary']['density']}")
```
