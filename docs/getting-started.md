# Getting Started with AcademicLint

This guide will help you get started with AcademicLint, the semantic clarity analyzer for academic writing.

## Installation

### Via pip

```bash
pip install academiclint
```

### Via pipx (recommended for CLI tools)

```bash
pipx install academiclint
```

### From source

```bash
git clone https://github.com/kase1111-hash/academiclint.git
cd academiclint
pip install -e .
```

## First Run

After installation, download the required NLP models:

```bash
academiclint setup
```

This downloads approximately 1.5GB of language models needed for analysis.

Verify the installation:

```bash
academiclint --version
```

## Basic Usage

### Analyze a file

```bash
academiclint check paper.md
```

### Analyze with specific strictness

```bash
academiclint check paper.md --level strict
```

### Output as JSON

```bash
academiclint check paper.md --format json > report.json
```

### Analyze from stdin

```bash
cat paper.md | academiclint check -
```

## Understanding the Output

AcademicLint analyzes your text and reports:

1. **Semantic Density Score** (0.0 - 1.0)
   - vapor (0.0-0.2): Almost no content
   - thin (0.2-0.4): Significant filler
   - adequate (0.4-0.6): Room for improvement
   - dense (0.6-0.8): Clear writing
   - crystalline (0.8-1.0): Exceptionally precise

2. **Flags** for specific issues:
   - UNDERSPECIFIED: Vague terms
   - UNSUPPORTED_CAUSAL: Causal claims without evidence
   - CIRCULAR: Circular definitions
   - WEASEL: Vague attribution
   - HEDGE_STACK: Excessive hedging
   - JARGON_DENSE: Too much unexplained jargon
   - CITATION_NEEDED: Claims needing sources
   - FILLER: Empty phrases

## Next Steps

- See [Configuration](configuration.md) for customizing analysis
- See [Domains](domains.md) for field-specific vocabulary
- See [API Reference](api-reference.md) for programmatic use
