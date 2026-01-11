# AcademicLint Technical Specification

> **Version**: 0.1.0
> **Python**: 3.11+
> **License**: Polyform Small Business 1.0.0

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Core Data Structures](#3-core-data-structures)
4. [Analysis Engine](#4-analysis-engine)
5. [Flag Types & Detection Logic](#5-flag-types--detection-logic)
6. [Semantic Density Calculation](#6-semantic-density-calculation)
7. [CLI Interface](#7-cli-interface)
8. [Python API](#8-python-api)
9. [REST API](#9-rest-api)
10. [Configuration System](#10-configuration-system)
11. [Domain Customization](#11-domain-customization)
12. [Output Formatters](#12-output-formatters)
13. [Model Management](#13-model-management)
14. [File Structure](#14-file-structure)
15. [Dependencies](#15-dependencies)
16. [Testing Strategy](#16-testing-strategy)

---

## 1. Overview

### 1.1 Purpose

AcademicLint is a semantic clarity analyzer that identifies:
- Vague/underspecified terms
- Unsupported causal claims
- Circular definitions
- Weasel words and hedge stacking
- Jargon overload
- Missing citations
- Low semantic density prose

### 1.2 Core Philosophy

- **Local-first**: All processing happens on-device by default
- **Privacy-respecting**: Zero telemetry, no cloud dependency
- **Extensible**: Domain customization for different academic fields
- **Actionable**: Every flag includes a suggestion for improvement

---

## 2. Architecture

### 2.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Entry Points                            │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│     CLI      │  Python API  │   REST API   │   LSP Server      │
│ (click/typer)│   (Library)  │   (FastAPI)  │  (pygls)          │
└──────┬───────┴──────┬───────┴──────┬───────┴────────┬──────────┘
       │              │              │                │
       ▼              ▼              ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Core Linter Engine                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Parser    │  │  Analyzer   │  │      Flag Generator     │  │
│  │ (Markdown,  │──│ (NLP Core)  │──│  (Rules + ML Hybrid)    │  │
│  │  LaTeX, txt)│  │             │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                          │                                      │
│  ┌───────────────────────┴──────────────────────────────────┐   │
│  │                    Detector Modules                       │   │
│  ├────────────┬────────────┬────────────┬──────────────────┤   │
│  │ Vagueness  │  Causal    │  Circular  │     Weasel       │   │
│  │ Detector   │  Detector  │  Detector  │    Detector      │   │
│  ├────────────┼────────────┼────────────┼──────────────────┤   │
│  │   Hedge    │  Jargon    │  Citation  │    Density       │   │
│  │  Detector  │  Detector  │  Detector  │   Calculator     │   │
│  └────────────┴────────────┴────────────┴──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Supporting Services                         │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│    Config    │    Domain    │    Model     │     Output        │
│    Loader    │   Manager    │   Manager    │   Formatters      │
└──────────────┴──────────────┴──────────────┴───────────────────┘
```

### 2.2 Data Flow

```
Input Text → Parser → Tokenization → Sentence Splitting →
  → Paragraph Segmentation → NLP Pipeline (spaCy/custom) →
  → Detector Modules (parallel) → Flag Aggregation →
  → Density Calculation → Result Assembly → Output Formatter
```

---

## 3. Core Data Structures

### 3.1 Flag

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class FlagType(Enum):
    UNDERSPECIFIED = "UNDERSPECIFIED"
    UNSUPPORTED_CAUSAL = "UNSUPPORTED_CAUSAL"
    CIRCULAR = "CIRCULAR"
    WEASEL = "WEASEL"
    HEDGE_STACK = "HEDGE_STACK"
    JARGON_DENSE = "JARGON_DENSE"
    CITATION_NEEDED = "CITATION_NEEDED"
    FILLER = "FILLER"

class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class Span:
    """Character-level position in source text."""
    start: int
    end: int

@dataclass
class Flag:
    """A single issue detected in the text."""
    type: FlagType
    term: str                          # The flagged text
    span: Span                         # Position in source
    line: int                          # 1-indexed line number
    column: int                        # 1-indexed column
    severity: Severity
    message: str                       # Human-readable explanation
    suggestion: str                    # How to fix it
    example_revision: Optional[str]    # Concrete rewrite example
    context: str                       # Surrounding text for display
```

### 3.2 Paragraph Result

```python
@dataclass
class ParagraphResult:
    """Analysis result for a single paragraph."""
    index: int                         # 0-indexed paragraph number
    text: str                          # Original paragraph text
    span: Span                         # Position in source
    density: float                     # 0.0 - 1.0
    flags: list[Flag]
    word_count: int
    sentence_count: int
```

### 3.3 Analysis Result

```python
@dataclass
class Summary:
    """Aggregate statistics for entire document."""
    density: float                     # Overall semantic density
    density_grade: str                 # "vapor", "thin", "adequate", "dense", "crystalline"
    flag_count: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    concept_count: int                 # Unique meaningful concepts
    filler_ratio: float                # Proportion of filler words
    suggestion_count: int

@dataclass
class AnalysisResult:
    """Complete analysis result for a document."""
    id: str                            # Unique check ID (e.g., "check_abc123")
    created_at: str                    # ISO 8601 timestamp
    input_length: int                  # Character count of input
    processing_time_ms: int

    summary: Summary
    paragraphs: list[ParagraphResult]
    overall_suggestions: list[str]     # Document-level recommendations

    # Convenience properties
    @property
    def density(self) -> float:
        return self.summary.density

    @property
    def flags(self) -> list[Flag]:
        """All flags across all paragraphs."""
        return [f for p in self.paragraphs for f in p.flags]
```

### 3.4 Configuration

```python
from pathlib import Path

@dataclass
class OutputConfig:
    format: str = "terminal"           # terminal, json, html, markdown, github
    color: bool = True
    show_suggestions: bool = True
    show_examples: bool = True

@dataclass
class Config:
    """Linter configuration."""
    level: str = "standard"            # relaxed, standard, strict, academic
    min_density: float = 0.50

    # Domain customization
    domain: Optional[str] = None       # Built-in domain name
    domain_file: Optional[Path] = None # Custom domain file path
    domain_terms: list[str] = None     # Inline domain terms

    # Custom patterns
    additional_weasels: list[str] = None
    ignore_patterns: list[str] = None

    # Processing options
    sections: Optional[list[str]] = None  # Only analyze these sections

    # Output
    output: OutputConfig = None

    # Thresholds (derived from level if not set)
    fail_under: Optional[float] = None    # Exit with error if below

    def __post_init__(self):
        if self.domain_terms is None:
            self.domain_terms = []
        if self.additional_weasels is None:
            self.additional_weasels = []
        if self.ignore_patterns is None:
            self.ignore_patterns = []
        if self.output is None:
            self.output = OutputConfig()
```

---

## 4. Analysis Engine

### 4.1 Linter Class

```python
class Linter:
    """Main entry point for text analysis."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize linter with configuration.

        Args:
            config: Linter configuration. Uses defaults if not provided.
        """
        self.config = config or Config()
        self._nlp = None  # Lazy-loaded NLP pipeline
        self._detectors = None  # Lazy-loaded detector modules

    def check(self, text: str) -> AnalysisResult:
        """
        Analyze text for semantic clarity issues.

        Args:
            text: The text to analyze (Markdown, plain text, or LaTeX)

        Returns:
            AnalysisResult with all findings
        """
        pass

    def check_file(self, path: Path) -> AnalysisResult:
        """
        Analyze a file.

        Args:
            path: Path to file (supports .md, .txt, .tex)

        Returns:
            AnalysisResult with all findings
        """
        pass

    def check_files(self, paths: list[Path]) -> dict[Path, AnalysisResult]:
        """
        Analyze multiple files.

        Args:
            paths: List of file paths

        Returns:
            Dict mapping paths to results
        """
        pass
```

### 4.2 NLP Pipeline

The analysis engine uses a multi-stage NLP pipeline:

```python
class NLPPipeline:
    """Core NLP processing pipeline."""

    def __init__(self, model_name: str = "en_core_web_lg"):
        self.nlp = spacy.load(model_name)
        # Add custom components
        self.nlp.add_pipe("sentence_quality", after="parser")

    def process(self, text: str) -> ProcessedDocument:
        """
        Process text through NLP pipeline.

        Returns:
            ProcessedDocument with tokens, sentences, entities, etc.
        """
        pass

@dataclass
class ProcessedDocument:
    """NLP-processed document ready for analysis."""
    text: str
    tokens: list[Token]
    sentences: list[Sentence]
    paragraphs: list[Paragraph]
    entities: list[Entity]
    noun_chunks: list[NounChunk]
    dependency_graph: DependencyGraph
```

### 4.3 Detector Interface

```python
from abc import ABC, abstractmethod

class Detector(ABC):
    """Base class for all detectors."""

    @abstractmethod
    def detect(
        self,
        doc: ProcessedDocument,
        config: Config
    ) -> list[Flag]:
        """
        Detect issues in the processed document.

        Args:
            doc: NLP-processed document
            config: Linter configuration

        Returns:
            List of detected flags
        """
        pass

    @property
    @abstractmethod
    def flag_types(self) -> list[FlagType]:
        """Flag types this detector can produce."""
        pass
```

---

## 5. Flag Types & Detection Logic

### 5.1 UNDERSPECIFIED

**Purpose**: Identify terms that sound meaningful but lack clear referents.

**Detection Strategies**:

1. **Known vague term list**: Match against curated list
   ```python
   VAGUE_TERMS = {
       "society", "things", "stuff", "aspects", "factors",
       "significant", "important", "interesting", "various",
       "some", "many", "most", "often", "sometimes",
       "impact", "affect", "influence", "change",
       "good", "bad", "positive", "negative",
       "dramatically", "significantly", "substantially",
   }
   ```

2. **Determiner analysis**: Flag "this", "that", "these" without clear antecedent

3. **Scope ambiguity**: Quantifiers without bounds
   - "people" (which people?)
   - "technology" (which technology?)
   - "recently" (when exactly?)

4. **Adjective vagueness scoring**: Use word embeddings to detect low-specificity modifiers

**Severity Mapping**:
| Context | Severity |
|---------|----------|
| In thesis statement | HIGH |
| In argument support | MEDIUM |
| In background/context | LOW |

### 5.2 UNSUPPORTED_CAUSAL

**Purpose**: Flag "X caused Y" claims without mechanism or evidence.

**Detection Strategies**:

1. **Causal verb detection**:
   ```python
   CAUSAL_VERBS = {
       "cause", "caused", "causes", "causing",
       "lead", "led", "leads", "leading",
       "result", "resulted", "results", "resulting",
       "produce", "produced", "produces", "producing",
       "create", "created", "creates", "creating",
       "drive", "drove", "drives", "driving",
       "trigger", "triggered", "triggers", "triggering",
   }
   ```

2. **Causal phrase patterns**:
   ```python
   CAUSAL_PATTERNS = [
       r"\b(because of|due to|owing to)\b",
       r"\b(as a result of|as a consequence of)\b",
       r"\b(leads? to|led to|leading to)\b",
       r"\b(results? in|resulted in|resulting in)\b",
   ]
   ```

3. **Citation proximity check**: Is there a citation within N tokens?

4. **Mechanism detection**: Check for "by", "through", "via" indicating mechanism

**Output**:
```
FLAG: "causes" → UNSUPPORTED_CAUSAL
  Correlation or causation?
  What is the proposed mechanism?
  Consider: "correlates with" or specify pathway
```

### 5.3 CIRCULAR

**Purpose**: Catch definitions that restate rather than clarify.

**Detection Strategies**:

1. **Morphological overlap**: Root form of defined term appears in definition
   ```python
   def is_circular(term: str, definition: str) -> bool:
       term_lemma = lemmatize(term)
       definition_lemmas = [lemmatize(w) for w in tokenize(definition)]
       return term_lemma in definition_lemmas
   ```

2. **Synonym detection**: Definition uses close synonym
   - Use WordNet synsets or embedding similarity

3. **Pattern matching**:
   ```python
   CIRCULAR_PATTERNS = [
       r"(\w+)\s+(is|means?|refers? to)\s+.*\b\1",  # X is ... X
       r"(\w+)\s+(is|means?)\s+(a|an|the)?\s*\1",   # X is X
   ]
   ```

**Example**:
```
"Freedom is the state of being free from oppression."

FLAG: CIRCULAR
  "Freedom" defined using "free"
  Consider: Define in terms of specific capabilities or absences
```

### 5.4 WEASEL

**Purpose**: Identify attribution that avoids accountability.

**Detection Strategies**:

1. **Pattern matching**:
   ```python
   WEASEL_PATTERNS = [
       r"\b(some|many|most|several|various)\s+(experts?|researchers?|scientists?|scholars?|studies|people)\b",
       r"\b(it is|it's)\s+(believed|thought|said|known|argued|claimed)\b",
       r"\b(research|studies?|evidence)\s+(shows?|suggests?|indicates?)\b(?!\s*\()",  # No citation following
       r"\bresearchers?\s+(have\s+)?(found|shown|demonstrated)\b(?!\s*\()",
       r"\baccording to\s+(some|many|most|experts?)\b",
   ]
   ```

2. **Citation verification**: Check if weasel phrase is followed by citation within 3 tokens

**Severity**: MEDIUM if followed by hedged claim, HIGH if followed by factual claim

### 5.5 HEDGE_STACK

**Purpose**: Detect excessive hedging that evacuates meaning.

**Detection Strategies**:

1. **Hedge word inventory**:
   ```python
   HEDGES = {
       "may", "might", "could", "possibly", "perhaps",
       "probably", "likely", "unlikely", "somewhat",
       "relatively", "apparently", "seemingly", "arguably",
       "tends to", "appears to", "seems to",
       "to some extent", "in some ways", "in a sense",
   }
   ```

2. **Hedge counting per clause**:
   ```python
   def count_hedges(clause: str) -> int:
       return sum(1 for h in HEDGES if h in clause.lower())

   # Flag if count >= 3 in single clause
   ```

3. **Confidence estimation**:
   ```python
   def estimate_confidence(hedge_count: int) -> float:
       """Estimate remaining confidence after hedging."""
       return 0.9 ** hedge_count  # Each hedge reduces by ~10%
   ```

**Example**:
```
"It could perhaps be argued that there may be some evidence
that possibly suggests..."

FLAG: HEDGE_STACK (5 hedges in one clause)
  Confidence: ~2%
  Consider: Make a claim or acknowledge uncertainty cleanly
```

### 5.6 JARGON_DENSE

**Purpose**: Alert when technical terms exceed explanation.

**Detection Strategies**:

1. **Technical term detection**:
   - Not in top 10,000 common words
   - Contains morphological complexity (affixes)
   - Domain-specific (cross-reference with domain terms)

2. **Explanation proximity**:
   - Check for definitional patterns nearby: "X, which means", "X (i.e.,", "X refers to"

3. **Density calculation**:
   ```python
   def jargon_density(sentence: str, domain_terms: set) -> float:
       tokens = tokenize(sentence)
       jargon_count = sum(1 for t in tokens if is_jargon(t, domain_terms))
       return jargon_count / len(tokens)

   # Flag if density > 0.3 without explanations
   ```

4. **Audience estimation**:
   ```python
   JARGON_AUDIENCE_LEVELS = {
       "undergraduate": 0.15,
       "graduate": 0.25,
       "specialist": 0.40,
   }
   ```

### 5.7 CITATION_NEEDED

**Purpose**: Identify claims that need sources but lack them.

**Detection Strategies**:

1. **Claim type detection**:
   ```python
   NEEDS_CITATION_PATTERNS = [
       r"\b\d+%\b",                          # Statistics
       r"\b(studies?|research)\s+(shows?|found)\b",
       r"\b(in|during|since)\s+\d{4}\b",     # Historical dates
       r"\baccording to\b(?!\s*\[)",         # Attribution without cite
       r"\b(first|largest|most|least)\b",   # Superlatives
   ]
   ```

2. **Citation detection**:
   ```python
   CITATION_PATTERNS = [
       r"\([A-Z][a-z]+,?\s+\d{4}\)",          # (Author, 2023)
       r"\([A-Z][a-z]+\s+et al\.,?\s+\d{4}\)", # (Author et al., 2023)
       r"\[\d+\]",                             # [1]
       r"\[[\w\s,]+\d{4}\]",                   # [Author 2023]
   ]
   ```

3. **Proximity check**: Is there a citation within the same sentence?

### 5.8 FILLER

**Purpose**: Identify phrases that add no information.

**Detection**:

```python
FILLER_PHRASES = [
    "in today's society",
    "in today's world",
    "throughout history",
    "since the dawn of time",
    "it is important to note that",
    "it is worth noting that",
    "it goes without saying",
    "needless to say",
    "it is clear that",
    "it is obvious that",
    "as we all know",
    "at the end of the day",
    "when all is said and done",
    "in terms of",
    "the fact that",
    "in order to",  # Can often just be "to"
]
```

---

## 6. Semantic Density Calculation

### 6.1 Definition

Semantic density measures the ratio of meaningful content to total text.

```
Density = Content Words / Total Words × Information Factor × Precision Factor
```

### 6.2 Components

1. **Content Word Ratio**:
   ```python
   FUNCTION_WORDS = {"the", "a", "an", "is", "are", "was", "were", ...}

   def content_word_ratio(tokens: list[str]) -> float:
       content = [t for t in tokens if t.lower() not in FUNCTION_WORDS]
       return len(content) / len(tokens)
   ```

2. **Information Factor** (TF-IDF inspired):
   ```python
   def information_factor(paragraph: str, document: str) -> float:
       """Higher score for paragraphs with unique/rare terms."""
       pass
   ```

3. **Precision Factor** (penalizes vagueness):
   ```python
   def precision_factor(flags: list[Flag]) -> float:
       """Lower score for more flags."""
       vague_count = sum(1 for f in flags if f.type == FlagType.UNDERSPECIFIED)
       return 1.0 / (1.0 + 0.1 * vague_count)
   ```

### 6.3 Density Grades

| Range | Grade | Description |
|-------|-------|-------------|
| 0.0 - 0.2 | vapor | Almost no content |
| 0.2 - 0.4 | thin | Significant filler |
| 0.4 - 0.6 | adequate | Room for improvement |
| 0.6 - 0.8 | dense | Clear writing |
| 0.8 - 1.0 | crystalline | Exceptionally precise |

### 6.4 Level-Specific Thresholds

| Level | Min Density | Flag Sensitivity |
|-------|-------------|------------------|
| relaxed | 0.30 | Only severe issues |
| standard | 0.50 | Common clarity issues |
| strict | 0.65 | All potential issues |
| academic | 0.75 | Comprehensive analysis |

---

## 7. CLI Interface

### 7.1 Commands

```bash
# Main command group
academiclint [OPTIONS] COMMAND [ARGS]

# Commands:
#   check    Analyze text for semantic clarity issues
#   setup    Download required models
#   serve    Start REST API server
#   version  Show version information
```

### 7.2 `check` Command

```bash
academiclint check [OPTIONS] FILE...

# Arguments:
#   FILE...    Files to analyze (supports glob patterns, use - for stdin)

# Options:
#   --level TEXT           Strictness level [relaxed|standard|strict|academic]
#   --format TEXT          Output format [terminal|json|html|markdown|github]
#   --min-density FLOAT    Minimum acceptable density (0.0-1.0)
#   --fail-under FLOAT     Exit with error if density below threshold
#   --domain TEXT          Use built-in domain vocabulary
#   --domain-file PATH     Use custom domain file
#   --sections TEXT        Comma-separated sections to analyze
#   --config PATH          Path to config file
#   --no-color             Disable colored output
#   --quiet                Only show summary
#   --verbose              Show detailed analysis
#   -o, --output PATH      Write output to file
#   --help                 Show help message
```

### 7.3 `setup` Command

```bash
academiclint setup [OPTIONS]

# Options:
#   --models TEXT    Specific models to download (comma-separated)
#   --force          Re-download even if exists
#   --offline        Configure for offline use only
#   --help           Show help message
```

### 7.4 `serve` Command

```bash
academiclint serve [OPTIONS]

# Options:
#   --host TEXT      Host to bind to [default: 127.0.0.1]
#   --port INTEGER   Port to bind to [default: 8080]
#   --reload         Enable auto-reload for development
#   --workers INT    Number of worker processes
#   --help           Show help message
```

### 7.5 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success, no issues or above threshold |
| 1 | Analysis found issues above severity threshold |
| 2 | Density below --fail-under threshold |
| 3 | Configuration error |
| 4 | File not found or unreadable |
| 5 | Model not installed (run setup) |

---

## 8. Python API

### 8.1 Basic Usage

```python
from academiclint import Linter, Config

# Default configuration
linter = Linter()
result = linter.check("Your text here...")

# Custom configuration
config = Config(
    level="strict",
    min_density=0.6,
    domain_terms=["epistemology", "ontology"]
)
linter = Linter(config)
result = linter.check(text)

# Access results
print(f"Density: {result.density}")
print(f"Grade: {result.summary.density_grade}")
print(f"Flags: {len(result.flags)}")

for flag in result.flags:
    print(f"  [{flag.type.value}] {flag.term}")
    print(f"    Line {flag.line}: {flag.message}")
    print(f"    Suggestion: {flag.suggestion}")
```

### 8.2 File Analysis

```python
from pathlib import Path

# Single file
result = linter.check_file(Path("paper.md"))

# Multiple files
results = linter.check_files([
    Path("chapter1.md"),
    Path("chapter2.md"),
])

for path, result in results.items():
    print(f"{path}: density={result.density:.2f}, flags={len(result.flags)}")
```

### 8.3 Streaming Analysis

```python
# For large documents, stream paragraph-by-paragraph
for paragraph_result in linter.check_stream(text):
    print(f"Paragraph {paragraph_result.index}: {paragraph_result.density:.2f}")
    for flag in paragraph_result.flags:
        print(f"  - {flag.type.value}: {flag.term}")
```

### 8.4 Configuration from File

```python
from academiclint import Config

# Load from YAML file
config = Config.from_file(".academiclint.yml")
linter = Linter(config)

# Merge with overrides
config = Config.from_file(".academiclint.yml", overrides={
    "level": "strict",
    "min_density": 0.7,
})
```

---

## 9. REST API

### 9.1 Endpoints

#### POST /v1/check

Analyze text for semantic clarity issues.

**Request**:
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

**Response**:
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
    "word_count": 287,
    "sentence_count": 15,
    "paragraph_count": 4,
    "concept_count": 8,
    "filler_ratio": 0.34,
    "suggestion_count": 9
  },

  "paragraphs": [
    {
      "index": 0,
      "text": "In today's society...",
      "span": {"start": 0, "end": 150},
      "density": 0.28,
      "word_count": 35,
      "sentence_count": 2,
      "flags": [
        {
          "type": "FILLER",
          "term": "In today's society",
          "span": {"start": 0, "end": 19},
          "line": 1,
          "column": 1,
          "severity": "medium",
          "message": "This phrase adds no specific information",
          "suggestion": "Remove or specify which society and time period",
          "example_revision": "In the United States since 2010...",
          "context": "In today's society, technology has..."
        }
      ]
    }
  ],

  "overall_suggestions": [
    "Document relies heavily on hedged language (12 instances)",
    "Consider specifying the scope in the introduction",
    "3 causal claims lack cited evidence"
  ]
}
```

#### GET /v1/health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "models_loaded": true
}
```

#### GET /v1/domains

List available built-in domains.

**Response**:
```json
{
  "domains": [
    {"name": "philosophy", "term_count": 245},
    {"name": "computer-science", "term_count": 512},
    {"name": "medicine", "term_count": 890},
    {"name": "law", "term_count": 367},
    {"name": "history", "term_count": 198}
  ]
}
```

### 9.2 Error Responses

```json
{
  "error": {
    "code": "INVALID_CONFIG",
    "message": "Unknown level 'extreme'. Valid options: relaxed, standard, strict, academic",
    "field": "config.level"
  }
}
```

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | INVALID_REQUEST | Malformed request body |
| 400 | INVALID_CONFIG | Invalid configuration value |
| 400 | TEXT_TOO_LONG | Text exceeds maximum length |
| 401 | UNAUTHORIZED | Missing or invalid API key |
| 429 | RATE_LIMITED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |
| 503 | MODELS_LOADING | Models still loading |

### 9.3 Rate Limits

| Tier | Requests/min | Max text length |
|------|--------------|-----------------|
| Free | 10 | 5,000 chars |
| Basic | 60 | 50,000 chars |
| Pro | 300 | 500,000 chars |
| Enterprise | Unlimited | Unlimited |

---

## 10. Configuration System

### 10.1 Configuration File Format

File: `.academiclint.yml`

```yaml
# Strictness level: relaxed, standard, strict, academic
level: standard

# Minimum semantic density (0.0 - 1.0)
min_density: 0.50

# Domain-specific vocabulary (won't flag as jargon)
domain: null  # or "philosophy", "computer-science", etc.
domain_terms:
  - epistemology
  - hermeneutics
  - phenomenological

# Custom weasel words to flag
additional_weasels:
  - "it goes without saying"
  - "needless to say"
  - "at the end of the day"

# Patterns to ignore (regex)
ignore_patterns:
  - "^Abstract:"          # Skip abstracts
  - "^References$"        # Skip reference sections
  - "^\\[\\d+\\]"        # Skip citation lines

# Sections to analyze (if specified, only these are checked)
sections: null  # or ["introduction", "conclusion", "discussion"]

# Output settings
output:
  format: terminal        # terminal, json, html, markdown, github
  color: true
  show_suggestions: true
  show_examples: true

# CI/CD settings
fail_under: null          # Exit with error if density below this
```

### 10.2 Configuration Precedence

1. CLI arguments (highest)
2. Environment variables (ACADEMICLINT_*)
3. Project config file (.academiclint.yml)
4. User config file (~/.config/academiclint/config.yml)
5. Default values (lowest)

### 10.3 Environment Variables

| Variable | Description |
|----------|-------------|
| ACADEMICLINT_LEVEL | Default strictness level |
| ACADEMICLINT_MIN_DENSITY | Default minimum density |
| ACADEMICLINT_API_KEY | API key for hosted service |
| ACADEMICLINT_CONFIG | Path to config file |
| ACADEMICLINT_NO_COLOR | Disable colored output |
| ACADEMICLINT_CACHE_DIR | Model cache directory |

---

## 11. Domain Customization

### 11.1 Built-in Domains

| Domain | Description | Term Count |
|--------|-------------|------------|
| philosophy | Philosophical terminology | ~245 |
| computer-science | CS and programming terms | ~512 |
| medicine | Medical and clinical terms | ~890 |
| law | Legal terminology | ~367 |
| history | Historical terms and periods | ~198 |
| psychology | Psychological terminology | ~423 |
| economics | Economic terms and concepts | ~287 |
| physics | Physics terminology | ~356 |
| biology | Biological terms | ~678 |
| sociology | Sociological concepts | ~312 |

### 11.2 Custom Domain File Format

```yaml
# my-domain.yml

# Domain metadata
name: "Cognitive Science"
description: "Interdisciplinary study of mind and cognition"
parent: psychology  # Inherit from built-in domain

# Terms that are precise in this field (won't be flagged as jargon)
technical_terms:
  - affordance
  - embodied cognition
  - enactivism
  - predictive processing
  - free energy principle
  - mental representation
  - intentionality

# Field-specific weasels to flag
domain_weasels:
  - "the brain wants"           # Anthropomorphization
  - "evolved to"                # Just-so story pattern
  - "is hardwired"              # Oversimplification

# Acceptable hedges in this field
permitted_hedges:
  - "the evidence suggests"
  - "one interpretation holds"
  - "current models indicate"

# Causal patterns acceptable in this field
accepted_causal_patterns:
  - "activates"                 # Neural activation
  - "encodes"                   # Information encoding

# Field-specific density expectations
density_baseline: 0.55
density_strict: 0.70

# Custom filler phrases for this field
domain_fillers:
  - "from a cognitive perspective"
  - "in terms of mental processes"
```

### 11.3 Domain Inheritance

Domains can inherit from parents:

```
medicine
├── clinical-medicine
├── pharmacology
└── psychiatry
    └── cognitive-science (custom)
```

Terms from parent domains are included automatically.

---

## 12. Output Formatters

### 12.1 Terminal (Default)

```
PARAGRAPH 3, LINE 47:

  "The French Revolution was caused by inequality and
   the desire for freedom."

  ├─ FLAG: "inequality" → UNDERSPECIFIED
  │   Economic? Legal? Social? Measured or perceived?
  │   Suggestion: Specify which dimension of inequality
  │
  ├─ FLAG: "desire for freedom" → UNDERSPECIFIED
  │   Freedom from what? For whom?
  │   Suggestion: Name the specific grievances of specific groups
  │
  └─ FLAG: "caused by" → UNSUPPORTED_CAUSAL
      Inequality existed for centuries. What changed?
      Suggestion: Identify the proximate trigger and mechanism

  DENSITY: 0.31 (below threshold 0.50)

═══════════════════════════════════════════════════════════════════
SUMMARY
───────────────────────────────────────────────────────────────────
  Overall Density:  0.43 (thin)
  Total Flags:      12
  Word Count:       287

  Flag Breakdown:
    UNDERSPECIFIED:     5
    UNSUPPORTED_CAUSAL: 3
    WEASEL:             2
    FILLER:             2
═══════════════════════════════════════════════════════════════════
```

### 12.2 JSON

See Section 9.1 for JSON schema.

### 12.3 HTML

Generates self-contained HTML report with:
- Highlighted text passages
- Interactive flag tooltips
- Density heat map visualization
- Summary statistics dashboard
- Collapsible suggestion panels

### 12.4 Markdown

```markdown
# AcademicLint Analysis Report

**File**: paper.md
**Date**: 2025-01-11
**Density**: 0.43 (thin)

## Summary

| Metric | Value |
|--------|-------|
| Overall Density | 0.43 |
| Total Flags | 12 |
| Word Count | 287 |

## Flags by Type

- UNDERSPECIFIED: 5
- UNSUPPORTED_CAUSAL: 3
- WEASEL: 2
- FILLER: 2

## Detailed Findings

### Paragraph 3 (Lines 45-52)

> "The French Revolution was caused by inequality and the desire for freedom."

**Flags**:

1. **UNDERSPECIFIED**: "inequality"
   - Economic? Legal? Social?
   - *Suggestion*: Specify which dimension

2. **UNSUPPORTED_CAUSAL**: "caused by"
   - What was the mechanism?
   - *Suggestion*: Identify the proximate trigger
```

### 12.5 GitHub Actions Format

```
::warning file=paper.md,line=47,col=5::UNDERSPECIFIED: "inequality" - Specify which dimension
::warning file=paper.md,line=47,col=35::UNSUPPORTED_CAUSAL: "caused by" - Identify mechanism
::error file=paper.md::Density 0.31 is below threshold 0.50
```

---

## 13. Model Management

### 13.1 Required Models

| Model | Size | Purpose |
|-------|------|---------|
| en_core_web_lg | ~780MB | Core NLP (tokenization, POS, NER, dependency parsing) |
| en_core_web_trf | ~500MB | Transformer-based (optional, higher accuracy) |
| sentence-transformers | ~420MB | Semantic similarity for circular detection |

### 13.2 Model Storage

```
~/.cache/academiclint/
├── models/
│   ├── spacy/
│   │   └── en_core_web_lg-3.7.0/
│   └── sentence-transformers/
│       └── all-MiniLM-L6-v2/
├── domains/
│   ├── philosophy.yml
│   ├── computer-science.yml
│   └── ...
└── config.json
```

### 13.3 Setup Command Implementation

```python
def setup(models: list[str] = None, force: bool = False):
    """Download and install required models."""

    default_models = ["en_core_web_lg", "all-MiniLM-L6-v2"]
    models = models or default_models

    for model in models:
        if model.startswith("en_core_web"):
            download_spacy_model(model, force=force)
        else:
            download_sentence_transformer(model, force=force)

    # Verify installation
    verify_models()
    print("Setup complete!")
```

---

## 14. File Structure

```
academiclint/
├── pyproject.toml              # Project metadata and dependencies
├── README.md
├── LICENSE.md
├── SPEC.md                     # This file
├── CONTRIBUTING.md
├── PRIVACY.md
│
├── src/
│   └── academiclint/
│       ├── __init__.py         # Public API exports
│       ├── __main__.py         # CLI entry point
│       ├── py.typed            # PEP 561 marker
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── linter.py       # Main Linter class
│       │   ├── config.py       # Configuration classes
│       │   ├── result.py       # Result data structures
│       │   ├── pipeline.py     # NLP pipeline
│       │   └── parser.py       # Document parsing
│       │
│       ├── detectors/
│       │   ├── __init__.py
│       │   ├── base.py         # Detector interface
│       │   ├── vagueness.py    # UNDERSPECIFIED detector
│       │   ├── causal.py       # UNSUPPORTED_CAUSAL detector
│       │   ├── circular.py     # CIRCULAR detector
│       │   ├── weasel.py       # WEASEL detector
│       │   ├── hedge.py        # HEDGE_STACK detector
│       │   ├── jargon.py       # JARGON_DENSE detector
│       │   ├── citation.py     # CITATION_NEEDED detector
│       │   └── filler.py       # FILLER detector
│       │
│       ├── density/
│       │   ├── __init__.py
│       │   └── calculator.py   # Semantic density calculation
│       │
│       ├── domains/
│       │   ├── __init__.py
│       │   ├── loader.py       # Domain file loading
│       │   ├── manager.py      # Domain management
│       │   └── builtin/        # Built-in domain definitions
│       │       ├── philosophy.yml
│       │       ├── computer-science.yml
│       │       ├── medicine.yml
│       │       └── ...
│       │
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py         # CLI command definitions
│       │   ├── check.py        # check command
│       │   ├── setup.py        # setup command
│       │   └── serve.py        # serve command
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py          # FastAPI application
│       │   ├── routes.py       # API routes
│       │   └── schemas.py      # Pydantic schemas
│       │
│       ├── formatters/
│       │   ├── __init__.py
│       │   ├── base.py         # Formatter interface
│       │   ├── terminal.py     # Terminal output
│       │   ├── json_.py        # JSON output
│       │   ├── html.py         # HTML report
│       │   ├── markdown.py     # Markdown output
│       │   └── github.py       # GitHub Actions format
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── manager.py      # Model download/management
│       │   └── cache.py        # Model caching
│       │
│       └── utils/
│           ├── __init__.py
│           ├── text.py         # Text utilities
│           └── patterns.py     # Regex patterns
│
├── tests/
│   ├── conftest.py
│   ├── test_linter.py
│   ├── test_config.py
│   ├── test_detectors/
│   │   ├── test_vagueness.py
│   │   ├── test_causal.py
│   │   └── ...
│   ├── test_density.py
│   ├── test_cli.py
│   ├── test_api.py
│   └── fixtures/
│       ├── sample_good.md
│       ├── sample_bad.md
│       └── ...
│
├── docs/
│   ├── getting-started.md
│   ├── configuration.md
│   ├── domains.md
│   ├── api-reference.md
│   └── self-hosting.md
│
└── examples/
    ├── basic_usage.py
    ├── custom_domain.py
    └── ci_integration/
        ├── github-action.yml
        └── pre-commit.yaml
```

---

## 15. Dependencies

### 15.1 Core Dependencies

```toml
[project]
dependencies = [
    "spacy>=3.7.0,<4.0.0",
    "click>=8.0.0",
    "pyyaml>=6.0",
    "rich>=13.0.0",           # Terminal formatting
    "pydantic>=2.0.0",        # Data validation
]
```

### 15.2 Optional Dependencies

```toml
[project.optional-dependencies]
api = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.23.0",
]
transformers = [
    "sentence-transformers>=2.2.0",
    "torch>=2.0.0",
]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",
    "mypy>=1.5.0",
    "ruff>=0.1.0",
    "pre-commit>=3.0.0",
]
```

### 15.3 spaCy Model Installation

```bash
# After pip install, download models
python -m spacy download en_core_web_lg
```

Or via setup command:

```bash
academiclint setup
```

---

## 16. Testing Strategy

### 16.1 Unit Tests

Test each detector independently with known inputs:

```python
# tests/test_detectors/test_vagueness.py

def test_detects_society():
    detector = VaguenessDetector()
    flags = detector.detect("In today's society, things have changed.")

    assert len(flags) >= 2
    terms = [f.term for f in flags]
    assert "society" in terms or "today's society" in terms
    assert "things" in terms

def test_domain_terms_not_flagged():
    config = Config(domain_terms=["epistemology"])
    detector = VaguenessDetector()
    flags = detector.detect("Epistemology is complex.", config)

    # "epistemology" should not be flagged as vague
    terms = [f.term for f in flags]
    assert "epistemology" not in terms
```

### 16.2 Integration Tests

Test full analysis pipeline:

```python
# tests/test_linter.py

def test_full_analysis():
    linter = Linter()
    result = linter.check("""
    In today's society, technology has had a significant impact.
    Many experts believe this is important.
    """)

    assert result.density < 0.5
    assert len(result.flags) >= 3
    assert any(f.type == FlagType.FILLER for f in result.flags)
    assert any(f.type == FlagType.WEASEL for f in result.flags)
```

### 16.3 Benchmark Tests

Compare against known-quality texts:

```python
# tests/test_benchmarks.py

def test_good_writing_high_density():
    with open("fixtures/sample_good.md") as f:
        text = f.read()

    result = Linter().check(text)
    assert result.density >= 0.6
    assert len(result.flags) <= 2

def test_bad_writing_flagged():
    with open("fixtures/sample_bad.md") as f:
        text = f.read()

    result = Linter().check(text)
    assert result.density < 0.4
    assert len(result.flags) >= 5
```

### 16.4 CLI Tests

```python
# tests/test_cli.py
from click.testing import CliRunner

def test_check_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "fixtures/sample.md"])

    assert result.exit_code == 0
    assert "DENSITY" in result.output

def test_check_with_json():
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "fixtures/sample.md", "--format", "json"])

    data = json.loads(result.output)
    assert "summary" in data
    assert "paragraphs" in data
```

### 16.5 API Tests

```python
# tests/test_api.py
from fastapi.testclient import TestClient

def test_check_endpoint():
    client = TestClient(app)
    response = client.post("/v1/check", json={
        "text": "Some vague text here.",
        "config": {"level": "standard"}
    })

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "paragraphs" in data
```

---

## Appendix A: Pattern Reference

### A.1 Vague Terms (Default List)

```python
VAGUE_TERMS = {
    # Pronouns/determiners
    "this", "that", "these", "those", "it", "they",

    # Vague nouns
    "thing", "things", "stuff", "aspect", "aspects",
    "factor", "factors", "issue", "issues", "matter",
    "element", "elements", "area", "areas",
    "society", "people", "individual", "individuals",

    # Vague adjectives
    "significant", "important", "interesting", "various",
    "certain", "particular", "specific", "general",
    "good", "bad", "positive", "negative",
    "big", "small", "large", "great",

    # Vague adverbs
    "very", "really", "quite", "rather", "somewhat",
    "fairly", "pretty", "extremely", "incredibly",
    "dramatically", "significantly", "substantially",
    "recently", "often", "sometimes", "usually",

    # Vague verbs
    "affect", "impact", "influence", "change",
    "involve", "relate", "concern",
}
```

### A.2 Weasel Patterns

```python
WEASEL_PATTERNS = [
    # Vague attribution
    r"\b(some|many|most|several|various|numerous)\s+"
    r"(experts?|researchers?|scientists?|scholars?|"
    r"studies|people|critics?|observers?)\b",

    # Passive voice hedging
    r"\b(it is|it's|it has been)\s+"
    r"(believed|thought|said|known|argued|claimed|suggested|"
    r"reported|noted|observed|shown|demonstrated|proven)\b",

    # Unattributed research
    r"\b(research|studies?|evidence|data)\s+"
    r"(shows?|suggests?|indicates?|demonstrates?|proves?)\b"
    r"(?!\s*[\(\[])",  # Not followed by citation

    # Vague consensus
    r"\b(according to|as per)\s+(some|many|most|experts?)\b",
    r"\bit is (widely|generally|commonly)\s+"
    r"(accepted|believed|known|thought)\b",
]
```

### A.3 Causal Patterns

```python
CAUSAL_PATTERNS = [
    r"\b(cause[sd]?|causing)\b",
    r"\b(lead[s]?|led|leading)\s+to\b",
    r"\b(result[s]?|resulted|resulting)\s+in\b",
    r"\b(produce[sd]?|producing)\b",
    r"\b(create[sd]?|creating)\b",
    r"\b(drive[s]?|drove|driving)\b",
    r"\b(trigger[s]?|triggered|triggering)\b",
    r"\b(because\s+of|due\s+to|owing\s+to)\b",
    r"\b(as\s+a\s+result\s+of|as\s+a\s+consequence\s+of)\b",
    r"\b(bring[s]?\s+about|brought\s+about)\b",
    r"\b(give[s]?\s+rise\s+to|gave\s+rise\s+to)\b",
]
```

---

## Appendix B: Density Calculation Details

### B.1 Full Algorithm

```python
def calculate_density(
    text: str,
    flags: list[Flag],
    config: Config
) -> float:
    """
    Calculate semantic density score for text.

    Components:
    1. Content word ratio (0.4 weight)
    2. Unique concept ratio (0.3 weight)
    3. Precision penalty (0.3 weight)

    Returns:
        Float between 0.0 and 1.0
    """
    tokens = tokenize(text)
    if len(tokens) == 0:
        return 0.0

    # 1. Content word ratio
    content_words = [t for t in tokens if t.lower() not in FUNCTION_WORDS]
    content_ratio = len(content_words) / len(tokens)

    # 2. Unique concept ratio (penalize repetition)
    lemmas = [lemmatize(t) for t in content_words]
    unique_ratio = len(set(lemmas)) / len(lemmas) if lemmas else 0

    # 3. Precision penalty (based on flags)
    flag_penalty = calculate_flag_penalty(flags, len(tokens))
    precision = 1.0 - flag_penalty

    # Weighted combination
    density = (
        0.4 * content_ratio +
        0.3 * unique_ratio +
        0.3 * precision
    )

    return min(1.0, max(0.0, density))


def calculate_flag_penalty(flags: list[Flag], token_count: int) -> float:
    """Calculate penalty based on flag count and severity."""
    weights = {
        Severity.LOW: 0.02,
        Severity.MEDIUM: 0.05,
        Severity.HIGH: 0.10,
    }

    total_penalty = sum(weights[f.severity] for f in flags)
    normalized = total_penalty / (token_count / 50)  # Per 50 tokens

    return min(0.5, normalized)  # Cap at 50% penalty
```

---

*End of Specification*
