# API Reference

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

## REST API (Planned)

A REST API server (`academiclint serve`) is planned for a future release. It will provide HTTP endpoints for text analysis using FastAPI. See the [project roadmap](../README.md#roadmap) for details.
