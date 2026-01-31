# Claude.md - AcademicLint

AcademicLint is a semantic clarity analyzer for academic writing. It uses NLP (spaCy) to detect issues like vagueness, unsupported causal claims, circular definitions, and filler phrases. It assigns a semantic density score (0.0-1.0) measuring information content vs. filler.

## Project Structure

```
src/academiclint/
├── core/           # Linter, NLP pipeline, config, results
├── detectors/      # Issue detection plugins (8 types)
├── formatters/     # Output formatters (terminal, JSON, HTML, markdown, GitHub)
├── cli/            # Click-based CLI (check, setup, serve commands)
└── utils/          # Patterns, validation, metrics, logging
tests/              # pytest tests (70% coverage minimum)
docs/               # Extended documentation
```

## Key Architecture Patterns

### Detector Plugin Pattern
All detectors inherit from the base class and implement `detect()`:

```python
# src/academiclint/detectors/base.py
class Detector(ABC):
    @abstractmethod
    def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
        pass
```

Existing detectors: `VaguenessDetector`, `CausalDetector`, `CircularDetector`, `WeaselDetector`, `HedgeDetector`, `JargonDetector`, `CitationDetector`, `FillerDetector`

### Formatter Strategy Pattern
All formatters inherit from base and implement `format()`:

```python
# src/academiclint/formatters/base.py
class Formatter(ABC):
    @abstractmethod
    def format(self, result: AnalysisResult) -> str:
        pass
```

### Data Flow
```
Text → NLPPipeline.process() → ProcessedDocument
     → Detector.detect() (for each) → Flag[]
     → Linter.check() → AnalysisResult
     → Formatter.format() → Output
```

### Lazy Loading
The NLP pipeline loads only when needed:
```python
def _ensure_pipeline(self) -> None:
    if self._nlp is None:
        self._nlp = NLPPipeline()
```

## Code Conventions

- **Line length**: 100 characters max
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Type hints**: Required on all public functions
- **Docstrings**: Google-style for public modules/classes/functions
- **Imports**: Sorted via ruff/isort

### Naming
| Type | Convention | Example |
|------|-----------|---------|
| Modules | snake_case | `vagueness_detector.py` |
| Classes | PascalCase | `VaguenessDetector` |
| Functions | snake_case | `detect_vague_terms()` |
| Constants | UPPER_SNAKE_CASE | `MAX_LINE_LENGTH` |
| Private | _leading_underscore | `_internal_method()` |

## Exception Hierarchy

All custom exceptions inherit from `AcademicLintError`:
- `ConfigurationError`
- `ValidationError`
- `ProcessingError`
- `DetectorError`
- `ParsingError`
- `ModelNotFoundError`
- `FormattingError`

## Key Data Structures

```python
# src/academiclint/core/result.py
AnalysisResult:
    id: str
    created_at: datetime
    summary: Summary (density, flag_count, word_count, concept_count)
    paragraphs: list[ParagraphResult]
        flags: list[Flag]
            type: FlagType
            term: str
            severity: Severity (info, warning, error)
            message: str
            suggestion: str
            context: str
```

## Common Modifications

### Adding a New Detector
1. Create `src/academiclint/detectors/yourdetector.py`
2. Inherit from `Detector` base class
3. Implement `detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]`
4. Register in `src/academiclint/detectors/__init__.py`
5. Add tests in `tests/test_detectors/`

### Adding a New Formatter
1. Create `src/academiclint/formatters/yourformatter.py`
2. Inherit from `Formatter` base class
3. Implement `format(self, result: AnalysisResult) -> str`
4. Register in `src/academiclint/formatters/__init__.py`

### Adding CLI Commands
CLI uses Click groups in `src/academiclint/cli/main.py`. Add new commands as separate modules in `cli/`.

## Configuration Levels

| Level | min_density | Use Case |
|-------|-------------|----------|
| relaxed | 0.30 | Blog posts |
| standard | 0.50 | Coursework |
| strict | 0.65 | Thesis |
| academic | 0.75 | Peer review |

## Testing

- Framework: pytest
- Minimum coverage: 70%
- Run tests: `pytest` or `make test`
- Test organization mirrors src/ structure

## Dependencies

- **spaCy 3.7+**: NLP processing
- **Click 8.0+**: CLI
- **Rich 13.0+**: Terminal output
- **Pydantic 2.0+**: Data validation
- **FastAPI 0.100+**: REST API (optional)

## Important Files

- `src/academiclint/core/linter.py`: Main entry point
- `src/academiclint/core/pipeline.py`: NLP processing
- `src/academiclint/utils/patterns.py`: Pattern definitions (VAGUE_TERMS, CAUSAL_PATTERNS, etc.)
- `pyproject.toml`: Project metadata and tool config
- `CONTRIBUTING.md`: Full developer guidelines
- `SPEC.md`: Detailed technical specification
