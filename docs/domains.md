# Domain Customization

Different academic fields have different vocabularies. AcademicLint supports domain customization to avoid flagging legitimate technical terminology as jargon.

## Built-in Domains

```bash
# Use a preset domain
academiclint check paper.md --domain philosophy
academiclint check paper.md --domain computer-science
academiclint check paper.md --domain medicine
academiclint check paper.md --domain law
academiclint check paper.md --domain history
```

Available built-in domains:

| Domain | Description | Term Count |
|--------|-------------|------------|
| philosophy | Philosophical terminology | ~50 |
| computer-science | CS and programming terms | ~80 |
| medicine | Medical and clinical terms | ~100 |
| law | Legal terminology | ~60 |
| history | Historical terms | ~40 |
| psychology | Psychological terminology | ~70 |
| economics | Economic concepts | ~50 |
| physics | Physics terminology | ~60 |
| biology | Biological terms | ~80 |
| sociology | Sociological concepts | ~50 |

## Custom Domain File

Create a custom domain YAML file:

```yaml
# my-domain.yml
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

Use your custom domain:

```bash
academiclint check paper.md --domain-file my-domain.yml
```

## Domain Inheritance

Domains can inherit from parent domains:

```
medicine
├── clinical-medicine
├── pharmacology
└── psychiatry
    └── cognitive-science (custom)
```

When using `parent: psychology`, your domain inherits all terms from the psychology domain.

## Inline Domain Terms

For quick additions without creating a file:

```yaml
# .academiclint.yml
domain_terms:
  - epistemology
  - hermeneutics
  - phenomenological
```

Or via CLI:

```bash
academiclint check paper.md --domain philosophy
```

## Python API

```python
from academiclint import Config, Linter

# Use built-in domain
config = Config(domain="philosophy")

# Use custom domain file
config = Config(domain_file="my-domain.yml")

# Add inline terms
config = Config(
    domain="philosophy",
    domain_terms=["qualia", "supervenience"]
)

linter = Linter(config)
result = linter.check(text)
```
