# Architecture & Data Flow

This document describes the architecture of AcademicLint, a semantic clarity analyzer for academic writing.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AcademicLint                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │     CLI      │    │   REST API   │    │ Python SDK   │   Entry Points    │
│  │  (Click)     │    │  (FastAPI)   │    │   (Import)   │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                   │
│         │                   │                   │                            │
│         └───────────────────┼───────────────────┘                            │
│                             ▼                                                │
│                   ┌─────────────────┐                                        │
│                   │     Linter      │              Core Engine               │
│                   │   (Orchestrator)│                                        │
│                   └────────┬────────┘                                        │
│                            │                                                 │
│         ┌──────────────────┼──────────────────┐                              │
│         ▼                  ▼                  ▼                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                        │
│  │   Parser    │   │  Pipeline   │   │   Config    │    Processing          │
│  │(MD/TXT/LaTeX)│   │   (NLP)    │   │  Manager    │                        │
│  └─────────────┘   └──────┬──────┘   └─────────────┘                        │
│                           │                                                  │
│                           ▼                                                  │
│         ┌─────────────────────────────────────┐                              │
│         │         Detector Pipeline           │         Analysis            │
│         ├─────────┬─────────┬─────────┬───────┤                              │
│         │Vagueness│ Causal  │ Weasel  │ ...   │                              │
│         └─────────┴─────────┴─────────┴───────┘                              │
│                           │                                                  │
│         ┌─────────────────┼─────────────────┐                                │
│         ▼                 ▼                 ▼                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│  │   Density   │  │   Domain    │  │   Result    │       Output             │
│  │ Calculator  │  │  Manager    │  │  Builder    │                          │
│  └─────────────┘  └─────────────┘  └──────┬──────┘                          │
│                                           │                                  │
│                                           ▼                                  │
│                              ┌─────────────────────┐                         │
│                              │     Formatters      │                         │
│                              ├──────┬──────┬───────┤                         │
│                              │ JSON │ HTML │Terminal│                        │
│                              └──────┴──────┴───────┘                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                Components                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Entry Layer   │     │   Core Layer    │     │  Output Layer   │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│                 │     │                 │     │                 │
│ • cli/          │     │ • core/         │     │ • formatters/   │
│   - main.py     │────▶│   - linter.py   │────▶│   - terminal.py │
│   - check.py    │     │   - config.py   │     │   - json_.py    │
│   - setup.py    │     │   - result.py   │     │   - html.py     │
│   - serve.py    │     │   - parser.py   │     │   - markdown.py │
│                 │     │   - pipeline.py │     │   - github.py   │
│ • api/          │     │   - exceptions.py     │                 │
│   - app.py      │     │   - environments.py   └─────────────────┘
│   - routes.py   │     │                 │
│   - schemas.py  │     └────────┬────────┘
│                 │              │
└─────────────────┘              ▼
                       ┌─────────────────┐     ┌─────────────────┐
                       │ Analysis Layer  │     │ Support Layer   │
                       ├─────────────────┤     ├─────────────────┤
                       │                 │     │                 │
                       │ • detectors/    │     │ • utils/        │
                       │   - vagueness   │     │   - validation  │
                       │   - causal      │     │   - patterns    │
                       │   - circular    │     │   - text        │
                       │   - weasel      │     │   - logging     │
                       │   - hedge       │     │   - metrics     │
                       │   - jargon      │     │   - env         │
                       │   - citation    │     │   - error_      │
                       │   - filler      │     │     reporting   │
                       │                 │     │                 │
                       │ • density/      │     │ • models/       │
                       │   - calculator  │     │   - manager     │
                       │                 │     │   - cache       │
                       │ • domains/      │     │                 │
                       │   - manager     │     └─────────────────┘
                       │   - loader      │
                       │   - builtin/    │
                       │                 │
                       └─────────────────┘
```

## Data Flow Diagram

### Analysis Request Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Input   │     │  Parse   │     │ Process  │     │ Analyze  │     │  Output  │
│   Text   │────▶│Document  │────▶│   NLP    │────▶│ Detectors│────▶│  Result  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │                │
     │                │                │                │                │
     ▼                ▼                ▼                ▼                ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│Raw text  │    │Paragraphs│    │Tokens,   │    │Flags with│    │Analysis  │
│(str)     │    │Sentences │    │POS tags, │    │positions,│    │Result    │
│          │    │Spans     │    │entities  │    │messages  │    │object    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Detailed Processing Pipeline

```
                                INPUT
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   Raw Text      │
                        │   (String)      │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
           ┌───────────────┐         ┌───────────────┐
           │ File Input    │         │ Direct Input  │
           │ (.md/.txt/.tex)│         │ (API/SDK)     │
           └───────┬───────┘         └───────┬───────┘
                   │                         │
                   └────────────┬────────────┘
                                │
                                ▼
                      ┌─────────────────┐
                      │     Parser      │
                      │  ┌───────────┐  │
                      │  │ Markdown  │  │
                      │  │ LaTeX     │  │
                      │  │ PlainText │  │
                      │  └───────────┘  │
                      └────────┬────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │ ProcessedDocument│
                     │  • paragraphs[]  │
                     │  • sentences[]   │
                     │  • spans[]       │
                     └────────┬─────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  NLP Pipeline   │
                    │  ┌───────────┐  │
                    │  │Tokenization│  │
                    │  │POS Tagging │  │
                    │  │NER         │  │
                    │  │Dependency  │  │
                    │  └───────────┘  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│Domain Manager │   │   Detectors   │   │   Density     │
│               │   │   (8 types)   │   │  Calculator   │
│ • Load domain │   │               │   │               │
│ • Get terms   │   │ • Vagueness   │   │ • Concept     │
│               │   │ • Causal      │   │   extraction  │
└───────┬───────┘   │ • Circular    │   │ • Filler      │
        │           │ • Weasel      │   │   ratio       │
        │           │ • Hedge       │   │ • Score calc  │
        │           │ • Jargon      │   │               │
        │           │ • Citation    │   └───────┬───────┘
        │           │ • Filler      │           │
        │           └───────┬───────┘           │
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                  ┌─────────────────┐
                  │  Result Builder │
                  │  ┌───────────┐  │
                  │  │ Flags[]   │  │
                  │  │ Summary   │  │
                  │  │ Paragraphs│  │
                  │  │ Suggestions│  │
                  │  └───────────┘  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   Formatters    │
                  │  ┌───────────┐  │
                  │  │ Terminal  │  │
                  │  │ JSON      │  │
                  │  │ HTML      │  │
                  │  │ Markdown  │  │
                  │  │ GitHub    │  │
                  │  └───────────┘  │
                  └────────┬────────┘
                           │
                           ▼
                        OUTPUT
```

## API Request Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         REST API Request Flow                             │
└──────────────────────────────────────────────────────────────────────────┘

  Client                    FastAPI                      Core
    │                          │                          │
    │  POST /v1/check          │                          │
    │  {text, config}          │                          │
    │─────────────────────────▶│                          │
    │                          │                          │
    │                          │  Validate Request        │
    │                          │  (Pydantic Schemas)      │
    │                          │                          │
    │                          │  Create Config           │
    │                          │─────────────────────────▶│
    │                          │                          │
    │                          │  Initialize Linter       │
    │                          │─────────────────────────▶│
    │                          │                          │
    │                          │  linter.check(text)      │
    │                          │─────────────────────────▶│
    │                          │                          │
    │                          │      Parse Document      │
    │                          │      ◄──────────────────▶│
    │                          │                          │
    │                          │      Run NLP Pipeline    │
    │                          │      ◄──────────────────▶│
    │                          │                          │
    │                          │      Execute Detectors   │
    │                          │      ◄──────────────────▶│
    │                          │                          │
    │                          │      Calculate Density   │
    │                          │      ◄──────────────────▶│
    │                          │                          │
    │                          │      Build Result        │
    │                          │◀─────────────────────────│
    │                          │                          │
    │                          │  Convert to Response     │
    │                          │  (CheckResponse)         │
    │                          │                          │
    │  200 OK                  │                          │
    │  {id, summary, ...}      │                          │
    │◀─────────────────────────│                          │
    │                          │                          │
```

## Detector Pipeline

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Detector Pipeline                                 │
└──────────────────────────────────────────────────────────────────────────┘

                    ProcessedDocument
                           │
                           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                    Detector Manager                           │
    │                                                               │
    │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
    │   │  Vagueness  │  │   Causal    │  │  Circular   │          │
    │   │  Detector   │  │  Detector   │  │  Detector   │          │
    │   │             │  │             │  │             │          │
    │   │ Detects:    │  │ Detects:    │  │ Detects:    │          │
    │   │ UNDER-      │  │ UNSUPPORTED_│  │ CIRCULAR    │          │
    │   │ SPECIFIED   │  │ CAUSAL      │  │ definitions │          │
    │   └─────┬───────┘  └─────┬───────┘  └─────┬───────┘          │
    │         │                │                │                   │
    │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
    │   │   Weasel    │  │    Hedge    │  │   Jargon    │          │
    │   │  Detector   │  │  Detector   │  │  Detector   │          │
    │   │             │  │             │  │             │          │
    │   │ Detects:    │  │ Detects:    │  │ Detects:    │          │
    │   │ WEASEL      │  │ HEDGE_STACK │  │ JARGON_     │          │
    │   │ words       │  │             │  │ DENSE       │          │
    │   └─────┬───────┘  └─────┬───────┘  └─────┬───────┘          │
    │         │                │                │                   │
    │   ┌─────────────┐  ┌─────────────┐                           │
    │   │  Citation   │  │   Filler    │                           │
    │   │  Detector   │  │  Detector   │                           │
    │   │             │  │             │                           │
    │   │ Detects:    │  │ Detects:    │                           │
    │   │ CITATION_   │  │ FILLER      │                           │
    │   │ NEEDED      │  │ phrases     │                           │
    │   └─────┬───────┘  └─────┬───────┘                           │
    │         │                │                                    │
    └─────────┼────────────────┼────────────────────────────────────┘
              │                │
              └────────┬───────┘
                       │
                       ▼
              ┌─────────────────┐
              │   Flag List     │
              │                 │
              │ • type          │
              │ • term          │
              │ • span          │
              │ • line/column   │
              │ • severity      │
              │ • message       │
              │ • suggestion    │
              │ • context       │
              └─────────────────┘
```

## Flag Types and Severity

| Flag Type | Description | Default Severity |
|-----------|-------------|------------------|
| UNDERSPECIFIED | Vague terms lacking precision | MEDIUM |
| UNSUPPORTED_CAUSAL | Causal claims without evidence | HIGH |
| CIRCULAR | Circular definitions | HIGH |
| WEASEL | Vague attribution (e.g., "some say") | MEDIUM |
| HEDGE_STACK | Excessive hedging language | LOW |
| JARGON_DENSE | Unexplained technical terms | MEDIUM |
| CITATION_NEEDED | Claims requiring citation | MEDIUM |
| FILLER | Empty phrases with no content | LOW |

## Density Calculation

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Semantic Density Calculation                         │
└──────────────────────────────────────────────────────────────────────────┘

                         Input Text
                              │
                              ▼
                    ┌─────────────────┐
                    │ Token Analysis  │
                    │                 │
                    │ • Extract nouns │
                    │ • Extract verbs │
                    │ • Identify      │
                    │   concepts      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌────────────┐
       │  Concept   │ │  Filler    │ │   Total    │
       │   Count    │ │   Count    │ │   Words    │
       └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                  ┌─────────────────┐
                  │    Calculate    │
                  │                 │
                  │ density =       │
                  │ concepts        │
                  │ ─────────────   │
                  │ total - filler  │
                  │                 │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Density Grade  │
                  │                 │
                  │ < 0.30: vapor   │
                  │ < 0.50: thin    │
                  │ < 0.70: adequate│
                  │ < 0.85: dense   │
                  │ ≥ 0.85: crystal │
                  └─────────────────┘
```

## Configuration Hierarchy

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Configuration Precedence                             │
│                        (Highest to Lowest)                                │
└──────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────┐
                    │   API Request       │  ◀── Highest Priority
                    │   Parameters        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   CLI Arguments     │
                    │   (--level, etc.)   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Environment       │
                    │   Variables         │
                    │   (ACADEMICLINT_*)  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Config File       │
                    │   (.academiclint.yml)│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Defaults          │  ◀── Lowest Priority
                    │   (Built-in)        │
                    └─────────────────────┘
```

## Environment Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Environment Configuration                            │
└──────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │                         DEVELOPMENT                                  │
  │  • Debug logging enabled                                            │
  │  • Verbose error messages                                           │
  │  • Hot reload support                                               │
  │  • Metrics: disabled                                                │
  └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │                          STAGING                                     │
  │  • Info-level logging                                               │
  │  • Production-like settings                                         │
  │  • Metrics: enabled (local)                                         │
  │  • Error reporting: enabled                                         │
  └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │                         PRODUCTION                                   │
  │  • Warning-level logging                                            │
  │  • Optimized performance                                            │
  │  • Metrics: enabled (exported)                                      │
  │  • Error reporting: Sentry integration                              │
  └─────────────────────────────────────────────────────────────────────┘
```

## File Structure

```
academiclint/
├── __init__.py              # Public API exports
├── __main__.py              # Module entry point
├── version.py               # Version management
│
├── api/                     # REST API (FastAPI)
│   ├── app.py              # Application factory
│   ├── routes.py           # Endpoint definitions
│   └── schemas.py          # Request/response models
│
├── cli/                     # Command-line interface
│   ├── main.py             # CLI entry point
│   ├── check.py            # Check command
│   ├── setup.py            # Setup command
│   └── serve.py            # Server command
│
├── core/                    # Core analysis engine
│   ├── linter.py           # Main Linter class
│   ├── config.py           # Configuration
│   ├── result.py           # Result structures
│   ├── parser.py           # Document parsing
│   ├── pipeline.py         # NLP processing
│   ├── environments.py     # Environment config
│   └── exceptions.py       # Custom exceptions
│
├── detectors/               # Issue detectors (8)
│   ├── base.py             # Abstract base class
│   ├── vagueness.py        # UNDERSPECIFIED
│   ├── causal.py           # UNSUPPORTED_CAUSAL
│   ├── circular.py         # CIRCULAR
│   ├── weasel.py           # WEASEL
│   ├── hedge.py            # HEDGE_STACK
│   ├── jargon.py           # JARGON_DENSE
│   ├── citation.py         # CITATION_NEEDED
│   └── filler.py           # FILLER
│
├── formatters/              # Output formatters (5)
│   ├── base.py             # Abstract base class
│   ├── terminal.py         # Console output
│   ├── json_.py            # JSON output
│   ├── html.py             # HTML reports
│   ├── markdown.py         # Markdown output
│   └── github.py           # GitHub Actions
│
├── domains/                 # Domain vocabularies
│   ├── manager.py          # Domain manager
│   ├── loader.py           # File loader
│   └── builtin/            # Built-in domains (10)
│
├── density/                 # Density calculation
│   └── calculator.py       # Scoring algorithm
│
├── models/                  # ML model management
│   ├── manager.py          # Model loader
│   └── cache.py            # Model caching
│
└── utils/                   # Utilities
    ├── validation.py       # Input validation
    ├── patterns.py         # Regex patterns
    ├── text.py             # Text processing
    ├── logging.py          # Logging setup
    ├── metrics.py          # Telemetry
    ├── env.py              # Environment vars
    └── error_reporting.py  # Error handling
```
