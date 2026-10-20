# Changelog

All notable changes to AcademicLint will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- LICENSE.md with PolyForm Small Business License 1.0.0
- LICENSE-SUMMARY.md with plain-English license explanation
- PRIVACY.md with comprehensive data handling policies
- CHANGELOG.md for version tracking
- FAQ section in documentation
- Troubleshooting guide

### Changed
- Without an explicit model, the NLP pipeline falls back from `en_core_web_lg`
  to `en_core_web_md` or `en_core_web_sm`, whichever is installed
- `check` accepts directories (searched recursively for supported files)
- Command-line options override `--config` values only when given; the config
  file's `output.format`, `output.color` and `fail_under` are now honoured
- Expected errors (bad input, bad config, missing model) print a one-line
  message and exit with code 1 instead of a traceback
- Files are checked independently: a file that cannot be analyzed is reported
  by name and the run continues (exit code 1 at the end); files without text
  found while expanding a directory are skipped with a warning
- `--sections` (or `sections:` in a config file) prints a warning that section
  filtering is not supported yet
- Reported line numbers for Markdown and LaTeX files (e.g. GitHub annotations)
  refer to the source file rather than the extracted text
- A heading directly followed by text is analyzed as a paragraph of its own
- `ModelLoadError` (a `ProcessingError`) is raised when spaCy or an installed
  model fails to load; the CLI stops once instead of failing every file
- A domain file's `parent` path is resolved relative to that file

### Fixed
- Text with leading whitespace lost its first sentence: 0 words and density 0.0
  for the first paragraph, and anchored patterns never matched it
- Sentences ran across blank lines (e.g. a Markdown heading into body text),
  giving the body paragraph 0 words and density 0.0
- Markdown list markers, block quotes and headings consumed the preceding blank
  line, merging paragraphs; `.markdown` files were not parsed as Markdown
- Flags starting in leading whitespace were dropped from `result.flags`
- Causal and weasel patterns matched across paragraphs (a "Results" heading
  followed by "In ..." was flagged as "results in")
- Circular definitions wrapped onto a second line were missed, an article was
  stripped from the start of a word ("an" from "anarchic"), and one sentence
  could be flagged twice
- Whitespace-only input is rejected with `ValidationError`
- `--domain` and `--domain-file` were ignored; unknown domains are now an error
- Multi-word and hyphenated domain terms (e.g. "machine learning",
  "cross-validation") never exempted jargon
- `--domain-file philosophy` read the built-in domain instead of the file
- Malformed config and domain files (non-mapping `output`, unknown output
  keys, values of the wrong type, non-UTF-8 text, empty or non-list term
  lists, a domain that inherits from itself) crashed with a traceback
- Non-UTF-8 stdin crashed with a traceback; so did text longer than spaCy
  accepts, which also stopped the remaining files
- A Markdown heading ending in '#' lost it ("C#" became "C")
- LaTeX citations were never recognised: `\cite{...}` became a placeholder no
  citation check matched, and `\citep`/`\parencite`/... were deleted, so every
  cited claim was flagged as needing a citation
- A `<` in Markdown prose (e.g. "p < .001") was taken for an HTML tag and the
  text up to the next `>` was deleted; an escaped `\$` in LaTeX was taken for
  math
- A multi-line `\cite`/`\ref`/`\label` split its sentence, and a LaTeX section
  title containing a command (`\emph{...}`) was cut short
- Domain terms joined by an apostrophe, slash, en dash or LaTeX `--` did not
  match their own spelling, while "machine, learning" matched "machine
  learning"
- `--quiet` had no effect (terminal and Markdown output); `check -` (stdin) was
  rejected
- GitHub output broke on newlines in messages and ignored `--min-density`
- `setup` ran `python -m spacy download`, which could use a different
  interpreter than academiclint; it now uses the running interpreter
- Reading stdin used `click.get_text_stream`, removed in Click 9
- Config, domain and `.env` files, `-o` output and redirected stdout used the
  platform's default encoding instead of UTF-8 (broke on Windows); a `.env`
  file starting with a byte-order mark lost its first variable

### Removed
- `safety` dev dependency (unused; `pip-audit` covers dependency scanning)

---

## [0.1.0] - 2026-01-11

### Added

#### Core Analysis Engine
- **Vagueness Detector** - Identifies terms lacking clear referents or scope
- **Causal Claim Detector** - Flags "X caused Y" statements without mechanism or evidence
- **Circular Definition Detector** - Catches self-referential definitions ("freedom means being free")
- **Weasel Word Detector** - Identifies attribution-avoiding phrases ("some experts say")
- **Hedge Stack Detector** - Flags excessive hedging that evacuates meaning
- **Jargon Density Detector** - Alerts when technical terms exceed explanation
- **Citation Gap Detector** - Identifies claims that need sources but lack them
- **Filler Detector** - Catches empty phrases ("in today's society")

#### Semantic Density
- Semantic density calculation (0.0-1.0 scale)
- Density grading: vapor, thin, adequate, dense, crystalline
- Per-paragraph and document-level density scores

#### CLI Tool
- `academiclint check` command for file analysis
- `academiclint setup` for model downloads
- Multiple strictness levels: relaxed, standard, strict, academic
- Section filtering with `--sections` flag
- Stdin support for piped input

#### Output Formats
- **Terminal** - Color-coded inline annotations
- **JSON** - Structured output for programmatic use
- **HTML** - Visual report with highlighted passages
- **Markdown** - Annotated version of original document
- **GitHub** - Format optimized for GitHub Actions annotations

#### Python Library
- `Linter` class for programmatic analysis
- `Config` class for customization
- Full type hints and dataclass-based results
- Async support for batch processing

#### REST API
- FastAPI-based HTTP server (`academiclint serve`)
- `/v1/check` endpoint for text analysis
- API key authentication support
- OpenAPI/Swagger documentation
- Postman collection for API testing

#### Configuration System
- YAML configuration file support (`.academiclint.yml`)
- Per-project configuration
- Domain-specific vocabulary files
- Custom weasel word lists
- Ignore pattern support

#### Domain Customization
- 10 built-in academic domains:
  - Philosophy
  - Computer Science
  - Medicine
  - Law
  - History
  - Psychology
  - Sociology
  - Physics
  - Biology
  - Economics
- Custom domain file support
- Domain inheritance (e.g., cognitive-science extends psychology)

#### Infrastructure
- Docker containerization with multi-stage builds
- GitHub Actions CI/CD pipeline
- Automated testing (unit, integration, system, regression)
- Performance benchmarks and load testing
- Static analysis (ruff, mypy, bandit)
- Security scanning for vulnerabilities

#### Documentation
- Comprehensive README with examples
- Technical specification (SPEC.md)
- API reference documentation
- Self-hosting guide
- Architecture diagrams
- Contributing guidelines

### Technical Details

#### Dependencies
- Python 3.11+
- spaCy for NLP processing
- FastAPI for REST API
- Click for CLI
- Pydantic for data validation

#### Models
- Custom semantic analysis models (~1.5GB)
- Automatic model download on first run
- Offline mode support

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 0.1.0 | 2026-01-11 | Initial release with core analysis engine |

---

## Upgrade Guide

### Upgrading to 0.1.0

This is the initial release. No upgrade steps required.

For future releases, upgrade guides will be provided here when breaking changes occur.

---

## Release Cadence

AcademicLint follows semantic versioning:
- **MAJOR** (x.0.0): Breaking API changes
- **MINOR** (0.x.0): New features, backward compatible
- **PATCH** (0.0.x): Bug fixes, backward compatible

We aim for:
- Monthly patch releases (bug fixes)
- Quarterly minor releases (new features)
- Major releases as needed (breaking changes)

---

## Links

- [GitHub Releases](https://github.com/kase1111-hash/academiclint/releases)
- [PyPI Package](https://pypi.org/project/academiclint/)
- [Documentation](https://docs.academiclint.dev)

[Unreleased]: https://github.com/kase1111-hash/academiclint/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kase1111-hash/academiclint/releases/tag/v0.1.0
