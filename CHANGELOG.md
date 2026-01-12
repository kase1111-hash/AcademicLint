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
- (none)

### Fixed
- (none)

### Removed
- (none)

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
