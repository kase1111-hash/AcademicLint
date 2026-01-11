# Contributing to AcademicLint

Thank you for your interest in contributing to AcademicLint! This document provides guidelines and standards for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

Be respectful, inclusive, and constructive. We welcome contributors of all experience levels.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/academiclint.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Download required models
python -m spacy download en_core_web_lg

# Run tests to verify setup
pytest
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with these specifications:

#### Formatting

- **Line length**: 100 characters maximum
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings (`"hello"`)
- **Imports**: Sorted with `isort` (handled by `ruff`)

#### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | `snake_case` | `vagueness_detector.py` |
| Classes | `PascalCase` | `VaguenessDetector` |
| Functions | `snake_case` | `detect_vague_terms()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_LINE_LENGTH` |
| Private | `_leading_underscore` | `_internal_method()` |

#### Type Hints

All public functions must have type hints:

```python
def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
    """Detect issues in the document.

    Args:
        doc: The processed document to analyze.
        config: Linter configuration.

    Returns:
        List of detected flags.
    """
    ...
```

#### Docstrings

Use Google-style docstrings for all public modules, classes, and functions:

```python
def calculate_density(text: str, flags: list[Flag], config: Config) -> float:
    """Calculate semantic density score for text.

    The density score combines content word ratio, unique concept ratio,
    and a precision penalty based on detected flags.

    Args:
        text: The text to analyze.
        flags: List of flags detected in the text.
        config: Linter configuration.

    Returns:
        Float between 0.0 and 1.0 representing semantic density.

    Raises:
        ValueError: If text is None.

    Example:
        >>> density = calculate_density("Hello world", [], Config())
        >>> 0.0 <= density <= 1.0
        True
    """
```

### Code Organization

#### File Structure

```
src/academiclint/
├── __init__.py         # Public API exports only
├── core/               # Core functionality
│   ├── __init__.py     # Module exports
│   ├── linter.py       # One class per file for major components
│   └── ...
├── detectors/          # Feature-specific modules
└── utils/              # Shared utilities
```

#### Import Order

```python
# 1. Standard library
import re
from pathlib import Path
from typing import Optional

# 2. Third-party packages
import spacy
from pydantic import BaseModel

# 3. Local imports
from academiclint.core.config import Config
from academiclint.core.result import Flag
```

### Error Handling

- Use specific exception types
- Provide helpful error messages
- Document exceptions in docstrings

```python
def check_file(self, path: Path) -> AnalysisResult:
    """Analyze a file.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file format is unsupported.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
```

### Logging

Use the `logging` module, not `print()`:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Processing paragraph %d", index)
logger.info("Analysis complete: %d flags found", len(flags))
logger.warning("Model not found, using fallback")
logger.error("Failed to parse file: %s", str(e))
```

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_linter.py           # Tests for main linter
├── test_detectors/          # Detector-specific tests
│   ├── test_vagueness.py
│   └── ...
└── fixtures/                # Test data files
```

### Writing Tests

```python
import pytest
from academiclint import Linter, Config


class TestLinter:
    """Tests for Linter class."""

    def test_initialization_with_defaults(self):
        """Test linter initializes with default configuration."""
        linter = Linter()
        assert linter.config.level == "standard"

    def test_check_returns_result(self, sample_text):
        """Test that check returns an AnalysisResult."""
        linter = Linter()
        result = linter.check(sample_text)
        assert result is not None
        assert result.id.startswith("check_")

    @pytest.mark.parametrize("level,expected_threshold", [
        ("relaxed", 0.30),
        ("standard", 0.50),
        ("strict", 0.65),
    ])
    def test_level_thresholds(self, level, expected_threshold):
        """Test threshold values for different levels."""
        config = Config(level=level)
        thresholds = config.get_level_thresholds()
        assert thresholds["min_density"] == expected_threshold
```

### Test Requirements

- All new features must have tests
- Maintain >80% code coverage
- Tests must pass before merging

Run tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=academiclint --cov-report=html

# Run specific test file
pytest tests/test_linter.py

# Run tests matching pattern
pytest -k "test_vagueness"
```

## Commit Guidelines

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat: Add hedge stacking detector

Implement detection of excessive hedging in text. The detector
identifies clauses with 3+ hedge words and calculates confidence
reduction.

Closes #42
```

```
fix: Correct line number calculation in flags

Line numbers were 0-indexed instead of 1-indexed, causing
incorrect positions in editor integrations.
```

## Pull Request Process

1. **Update documentation** for any changed functionality
2. **Add tests** for new features or bug fixes
3. **Run the full test suite**: `pytest`
4. **Run linting**: `pre-commit run --all-files`
5. **Update CHANGELOG.md** if applicable
6. **Request review** from maintainers

### PR Title Format

Same as commit message: `<type>: <description>`

### PR Description Template

```markdown
## Summary
Brief description of changes.

## Changes
- Change 1
- Change 2

## Testing
How was this tested?

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG updated (if applicable)
- [ ] Pre-commit hooks pass
```

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Email: kase1111@gmail.com

Thank you for contributing!
