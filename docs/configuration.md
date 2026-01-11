# Configuration

AcademicLint can be configured through a YAML file, environment variables, or command-line arguments.

## Configuration File

Create `.academiclint.yml` in your project root:

```yaml
# Strictness: relaxed, standard, strict, academic
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

# Patterns to ignore (regex)
ignore_patterns:
  - "^Abstract:"
  - "^References$"

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

## Strictness Levels

| Level | Use Case | Density Threshold | Flags |
|-------|----------|-------------------|-------|
| `relaxed` | Blog posts, informal writing | 0.30 | Only severe issues |
| `standard` | Coursework, general academic | 0.50 | Common clarity issues |
| `strict` | Thesis, journal submission | 0.65 | All potential issues |
| `academic` | Peer review preparation | 0.75 | Comprehensive analysis |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ACADEMICLINT_LEVEL` | Default strictness level |
| `ACADEMICLINT_MIN_DENSITY` | Default minimum density |
| `ACADEMICLINT_CONFIG` | Path to config file |
| `ACADEMICLINT_NO_COLOR` | Disable colored output |
| `ACADEMICLINT_CACHE_DIR` | Model cache directory |

## Configuration Precedence

1. CLI arguments (highest)
2. Environment variables
3. Project config file (`.academiclint.yml`)
4. User config file (`~/.config/academiclint/config.yml`)
5. Default values (lowest)

## Python API Configuration

```python
from academiclint import Config, Linter, OutputConfig

# Create configuration
config = Config(
    level="strict",
    min_density=0.6,
    domain="philosophy",
    domain_terms=["epistemology", "ontology"],
    output=OutputConfig(format="json", color=False),
)

# Use with linter
linter = Linter(config)
result = linter.check("Your text here...")
```

## Loading from File

```python
from academiclint import Config

# Load from YAML
config = Config.from_file(".academiclint.yml")

# Load with overrides
config = Config.from_file(".academiclint.yml", overrides={
    "level": "strict",
    "min_density": 0.7,
})
```
