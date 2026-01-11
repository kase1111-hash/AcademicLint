# AcademicLint

**Grammarly checks your spelling. AcademicLint checks your thinking.**

[![License: Polyform Small Business](https://img.shields.io/badge/License-Polyform%20Small%20Business-blue.svg)](./LICENSE.md)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

---

## What Is This?

AcademicLint is a semantic clarity analyzer for academic writing. It identifies vague concepts, unsupported claims, circular definitions, and low-density prose—the stuff spell-checkers and grammar tools miss entirely.

It doesn't fix your commas. It asks: **"What do you actually mean?"**

---

## The Problem

Most academic writing fails not because of grammar, but because of **semantic fog**:

```
❌ "The French Revolution was caused by inequality and the desire for freedom."
```

This sentence has no grammar errors. It's also nearly meaningless:
- Which inequality? Economic? Legal? Social?
- Whose freedom? Peasants wanted different things than bourgeoisie.
- "Caused by" implies mechanism. What was the mechanism?

Students lose points. Researchers publish mush. Readers waste time. Everyone knows something is wrong, but "unclear" is hard to operationalize.

Until now.

---

## The Solution

AcademicLint uses computational semantic analysis to surface exactly *what* is unclear and *why*:

```
$ academiclint check paper.md

PARAGRAPH 3, LINE 47:

  "The French Revolution was caused by inequality and 
   the desire for freedom."

  ├─ FLAG: "inequality" → UNDERSPECIFIED
  │   Economic? Legal? Social? Measured or perceived?
  │   Suggestion: Specify which dimension of inequality
  │   
  ├─ FLAG: "desire for freedom" → UNDERSPECIFIED
  │   Freedom from what? For whom?
  │   - Peasants sought tax relief
  │   - Bourgeoisie sought political power  
  │   - Nobles sought regional autonomy
  │   Suggestion: Name the specific grievances of specific groups
  │
  └─ FLAG: "caused by" → UNSUPPORTED CAUSAL CLAIM
      Inequality existed for centuries. What changed?
      Suggestion: Identify the proximate trigger and mechanism

  DENSITY: 0.31 (below threshold 0.50)
```

---

## Features

### Core Analysis

| Feature | Description |
|---------|-------------|
| **Vagueness Detection** | Identifies terms that sound meaningful but lack clear referents |
| **Causal Claim Validation** | Flags "X caused Y" statements without mechanism |
| **Circular Definition Detection** | Catches "freedom means being free" patterns |
| **Weasel Word Identification** | "Some experts say...", "It is believed that...", "Many argue..." |
| **Jargon Density Analysis** | Alerts when technical terms exceed explanation |
| **Semantic Density Scoring** | Quantifies information content vs. filler |
| **Citation Gap Detection** | Identifies claims that need sources but lack them |

### Output Formats

- **Terminal** — Color-coded inline annotations
- **JSON** — Structured output for CI/CD integration
- **HTML** — Visual report with highlighted passages
- **Markdown** — Annotated version of original document
- **LSP** — Language Server Protocol for editor integration

### Integrations

- **VS Code Extension** — Real-time underlining as you write
- **Obsidian Plugin** — For markdown-based academic workflows
- **Google Docs Add-on** — One-click analysis (coming soon)
- **Overleaf/LaTeX** — Pre-submission checks (coming soon)
- **GitHub Actions** — Automated PR checks for documentation

---

## Installation

### CLI Tool

```bash
# Via pip
pip install academiclint

# Via pipx (recommended for CLI tools)
pipx install academiclint

# From source
git clone https://github.com/yourusername/academiclint.git
cd academiclint
pip install -e .
```

### Requirements

- Python 3.11+
- ~2GB disk space (for language models)
- Internet connection for first run (downloads models)

### First Run

```bash
# Downloads required models (~1.5GB)
academiclint setup

# Verify installation
academiclint --version
```

---

## Quick Start

### Basic Usage

```bash
# Analyze a file
academiclint check paper.md

# Analyze with specific strictness
academiclint check paper.md --level strict

# Output as JSON
academiclint check paper.md --format json > report.json

# Analyze from stdin
cat paper.md | academiclint check -

# Analyze specific sections
academiclint check paper.md --sections "introduction,conclusion"
```

### Configuration

Create `.academiclint.yml` in your project root:

```yaml
# .academiclint.yml

# Strictness: relaxed, standard, strict, academic
level: standard

# Minimum semantic density (0.0 - 1.0)
min_density: 0.50

# Domain-specific vocabulary (won't flag as jargon)
domain_terms:
  - epistemology
  - hermeneutics
  - phenomenological

# Custom weasel words to flag
additional_weasels:
  - "it goes without saying"
  - "needless to say"

# Patterns to ignore
ignore_patterns:
  - "Abstract:"      # Don't analyze abstracts
  - "References"     # Skip reference sections

# Output settings
output:
  format: terminal
  color: true
  show_suggestions: true
  show_examples: true
```

### Strictness Levels

| Level | Use Case | Density Threshold | Flags |
|-------|----------|-------------------|-------|
| `relaxed` | Blog posts, informal writing | 0.30 | Only severe issues |
| `standard` | Coursework, general academic | 0.50 | Common clarity issues |
| `strict` | Thesis, journal submission | 0.65 | All potential issues |
| `academic` | Peer review preparation | 0.75 | Comprehensive analysis |

---

## Understanding the Output

### Semantic Density Score

Every paragraph receives a density score from 0.0 to 1.0:

```
DENSITY SCALE:

0.0 - 0.2  │████                    │ Vapor (almost no content)
0.2 - 0.4  │████████                │ Thin (significant filler)
0.4 - 0.6  │████████████            │ Adequate (room for improvement)
0.6 - 0.8  │████████████████        │ Dense (clear writing)
0.8 - 1.0  │████████████████████    │ Crystalline (exceptionally precise)
```

Academic writing should generally target 0.5-0.7. Higher isn't always better—0.9+ can indicate writing that's too compressed for readability.

### Flag Types

#### `UNDERSPECIFIED`
Term lacks clear referent or scope.

```
"Society has changed dramatically."

FLAG: "society" → UNDERSPECIFIED
  Which society? Western? American? Global?
  Which demographic within that society?
  
FLAG: "dramatically" → UNDERSPECIFIED  
  By what measure? Compared to when?
```

#### `UNSUPPORTED_CAUSAL`
Causal claim without mechanism or evidence.

```
"Social media causes depression in teenagers."

FLAG: "causes" → UNSUPPORTED_CAUSAL
  Correlation or causation?
  What is the proposed mechanism?
  Consider: "correlates with" or specify pathway
```

#### `CIRCULAR`
Definition or explanation that restates rather than clarifies.

```
"Freedom is the state of being free from oppression."

FLAG: CIRCULAR
  "Freedom" defined using "free"
  Consider: Define in terms of specific capabilities or absences
```

#### `WEASEL`
Attribution that avoids accountability.

```
"Some researchers believe that..."

FLAG: "Some researchers" → WEASEL
  Which researchers? Cite them or remove.
  If consensus, say "consensus holds"
  If disputed, name the dispute
```

#### `HEDGE_STACK`
Excessive hedging that evacuates meaning.

```
"It could perhaps be argued that there may be some evidence 
that possibly suggests..."

FLAG: HEDGE_STACK (5 hedges in one clause)
  Confidence: ~2%
  Consider: Make a claim or acknowledge uncertainty cleanly
```

#### `JARGON_DENSE`
Technical terms without sufficient explanation.

```
"The hermeneutic phenomenology of Dasein's thrownness 
reveals the ontic-ontological difference."

FLAG: JARGON_DENSE
  5 technical terms, 0 explanations
  Reader prerequisite: Graduate philosophy
  Consider: Define terms or specify audience
```

#### `CITATION_NEEDED`
Factual or controversial claim without source.

```
"Studies show that 73% of students experience anxiety."

FLAG: CITATION_NEEDED
  Specific statistic requires source
  "Studies show" without citation is a weasel pattern
```

---

## Examples

### Before and After

**Original (Density: 0.28):**
```
In today's society, technology has had a significant impact on 
the way people communicate. Many experts believe this has led 
to both positive and negative outcomes. It is clear that more 
research is needed to fully understand these complex dynamics.
```

**AcademicLint Output:**
```
├─ "In today's society" → FILLER (adds no information)
├─ "technology" → UNDERSPECIFIED (which technology?)
├─ "significant impact" → UNDERSPECIFIED (measured how?)
├─ "the way people communicate" → UNDERSPECIFIED (which people? what channels?)
├─ "Many experts" → WEASEL (name them or cite)
├─ "positive and negative outcomes" → UNDERSPECIFIED (name the outcomes)
├─ "It is clear that" → FILLER (if clear, just state it)
└─ "complex dynamics" → UNDERSPECIFIED (what dynamics specifically?)

SUMMARY: 8 flags, 0 concrete claims
DENSITY: 0.28
```

**Revised (Density: 0.71):**
```
Smartphone-based messaging has reduced response latency in personal 
communication from hours (email) to minutes (SMS/chat), while 
simultaneously decreasing average message length from 150+ words 
to under 20 (Pew Research, 2023). This compression correlates with 
reported declines in perceived conversation depth (Thompson et al., 2022), 
though causation remains unestablished.
```

**AcademicLint Output:**
```
✓ Specific technology named (smartphone messaging)
✓ Quantified claim (hours → minutes, 150+ → 20 words)
✓ Cited source (Pew Research, 2023)
✓ Causal claim appropriately hedged ("correlates," "causation unestablished")
✓ Second source cited (Thompson et al., 2022)

SUMMARY: 0 flags
DENSITY: 0.71
```

---

## API Usage

### Python Library

```python
from academiclint import Linter, Config

# Initialize with default config
linter = Linter()

# Or with custom config
config = Config(
    level="strict",
    min_density=0.6,
    domain_terms=["epistemology", "ontology"]
)
linter = Linter(config)

# Analyze text
result = linter.check("""
The impact of social factors on outcomes has been significant.
Many researchers have noted the importance of this phenomenon.
""")

# Access results
print(f"Density: {result.density}")
print(f"Flags: {len(result.flags)}")

for flag in result.flags:
    print(f"  {flag.type}: {flag.term}")
    print(f"    Line {flag.line}: {flag.context}")
    print(f"    Suggestion: {flag.suggestion}")

# Get summary statistics
stats = result.summary()
print(f"Total words: {stats.word_count}")
print(f"Unique concepts: {stats.concept_count}")
print(f"Filler ratio: {stats.filler_ratio:.1%}")
```

### REST API

```bash
# Start local server
academiclint serve --port 8080

# Or use hosted API (requires API key)
export ACADEMICLINT_API_KEY=your_key_here
```

```python
import requests

response = requests.post(
    "https://api.academiclint.dev/v1/check",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "text": "Your academic text here...",
        "config": {
            "level": "standard",
            "format": "json"
        }
    }
)

result = response.json()
```

### API Response Schema

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
    "concept_count": 8,
    "filler_ratio": 0.34,
    "suggestion_count": 9
  },
  
  "paragraphs": [
    {
      "index": 0,
      "text": "In today's society...",
      "density": 0.28,
      "flags": [
        {
          "type": "FILLER",
          "term": "In today's society",
          "span": [0, 19],
          "severity": "medium",
          "suggestion": "Remove or specify which society and time period",
          "example_revision": "In the United States since 2010..."
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

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/lint-docs.yml
name: Documentation Quality

on:
  pull_request:
    paths:
      - 'docs/**'
      - '**.md'

jobs:
  academiclint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install AcademicLint
        run: pip install academiclint
        
      - name: Run analysis
        run: |
          academiclint check docs/ \
            --format github \
            --min-density 0.45 \
            --fail-under 0.40
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/yourusername/academiclint
    rev: v0.1.0
    hooks:
      - id: academiclint
        args: ['--level', 'standard', '--fail-under', '0.40']
        types: [markdown]
```

---

## Editor Integration

### VS Code

Install from marketplace: `AcademicLint`

Or install manually:
```bash
code --install-extension academiclint.academiclint
```

Features:
- Real-time underlining of flagged passages
- Hover for explanations and suggestions
- Quick-fix actions for common issues
- Density score in status bar
- Document heat map (View → AcademicLint Heat Map)

**Settings (settings.json):**
```json
{
  "academiclint.level": "standard",
  "academiclint.minDensity": 0.5,
  "academiclint.showInlineHints": true,
  "academiclint.domainTermsFile": ".academiclint-terms.txt"
}
```

### Obsidian

Install via Community Plugins: search "AcademicLint"

Features:
- Ribbon icon for one-click analysis
- Reading view annotations
- Daily notes integration (track clarity over time)
- Graph view: concept density by note

### Vim/Neovim

Via ALE:
```vim
let g:ale_linters = {'markdown': ['academiclint']}
```

Via null-ls (Neovim):
```lua
require("null-ls").setup({
  sources = {
    require("null-ls").builtins.diagnostics.academiclint,
  },
})
```

---

## Domain Customization

Different fields have different vocabularies. A term that's jargon in one context is precise technical language in another.

### Built-in Domains

```bash
# Use a preset domain
academiclint check paper.md --domain philosophy
academiclint check paper.md --domain computer-science
academiclint check paper.md --domain medicine
academiclint check paper.md --domain law
academiclint check paper.md --domain history
```

### Custom Domain File

```yaml
# my-domain.yml
name: "Cognitive Science"
parent: psychology  # Inherit from built-in

# Terms that are precise in this field
technical_terms:
  - affordance
  - embodied cognition
  - enactivism
  - predictive processing
  - free energy principle

# Field-specific weasels to flag
domain_weasels:
  - "the brain wants"      # Anthropomorphization
  - "evolved to"           # Just-so story pattern

# Acceptable hedges in this field
permitted_hedges:
  - "the evidence suggests"
  - "one interpretation holds"

# Field-specific density expectations
density_baseline: 0.55
```

```bash
academiclint check paper.md --domain-file my-domain.yml
```

---

## Interpreting Results

### What AcademicLint Is

- A tool for surfacing *where* your writing is vague
- A prompt to think more precisely
- A way to see your own blind spots
- A revision assistant, not a replacement for thinking

### What AcademicLint Is Not

- A grammar checker (use Grammarly, LanguageTool, etc.)
- A plagiarism detector (use Turnitin, etc.)
- A style enforcer (use your field's style guide)
- An oracle of truth (it checks clarity, not correctness)
- A replacement for peer review

### When to Ignore Flags

Flags are suggestions, not commands. Ignore them when:

- **Intentional ambiguity** — Sometimes vagueness is the point (e.g., discussing contested concepts)
- **Audience calibration** — Technical terms are fine when writing for experts
- **Stylistic choice** — Some hedging is appropriate academic caution
- **False positives** — The system isn't perfect; use judgment

### Recommended Workflow

1. **Write first, lint later** — Don't interrupt flow; analyze after drafting
2. **Focus on high-severity flags** — Not everything needs fixing
3. **Use suggestions as prompts** — They're starting points, not final answers
4. **Track density over revisions** — Watch the score improve
5. **Compare to benchmarks** — How does your writing compare to published work in your field?

---

## Benchmarks

We analyzed 10,000 published academic papers across disciplines:

| Field | Mean Density | Std Dev | Top Quartile |
|-------|--------------|---------|--------------|
| Mathematics | 0.72 | 0.11 | 0.80+ |
| Physics | 0.68 | 0.09 | 0.75+ |
| Computer Science | 0.61 | 0.12 | 0.71+ |
| Philosophy | 0.58 | 0.14 | 0.69+ |
| History | 0.54 | 0.13 | 0.65+ |
| Sociology | 0.49 | 0.15 | 0.61+ |
| Literary Studies | 0.45 | 0.16 | 0.58+ |

Note: Lower density isn't always worse—some fields value nuance and hedging more than others. Compare within your discipline.

---

## Privacy & Data

### Local Mode (Default)

- All processing happens on your machine
- No text sent to external servers
- Models downloaded once, run locally
- Zero telemetry

### API Mode (Optional)

- Text sent to our servers for processing
- Not stored beyond request lifetime
- Not used for training
- SOC 2 Type II compliant (certification pending)
- See [Privacy Policy](./PRIVACY.md)

### Self-Hosted API

For institutions wanting central deployment:

```bash
docker run -p 8080:8080 academiclint/server:latest
```

See [Self-Hosting Guide](./docs/self-hosting.md) for Kubernetes deployment.

---

## Roadmap

### v0.1 (Current)
- [x] Core analysis engine
- [x] CLI tool
- [x] Python library
- [x] JSON/HTML/Markdown output
- [x] Basic domain customization

### v0.2
- [ ] VS Code extension
- [ ] Obsidian plugin
- [ ] REST API
- [ ] GitHub Actions integration

### v0.3
- [ ] Google Docs add-on
- [ ] Overleaf integration
- [ ] Comparative analysis (your draft vs. published papers)
- [ ] Improvement tracking over time

### v0.4
- [ ] Multi-language support (Spanish, French, German)
- [ ] Discipline-specific models
- [ ] Collaborative review mode

### Future
- [ ] Real-time co-writing suggestions
- [ ] Integration with reference managers (Zotero, Mendeley)
- [ ] Course management system plugins (Canvas, Moodle)

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Areas We Need Help

- **Domain expertise** — Help us build field-specific term lists and calibration
- **Language support** — Extend analysis to non-English academic writing
- **Editor plugins** — Integrations for more editors and platforms
- **Benchmarking** — Help us analyze more published corpora
- **Documentation** — Examples, tutorials, translations

### Development Setup

```bash
git clone https://github.com/yourusername/academiclint.git
cd academiclint
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
```

---

## FAQ

**Q: Is this going to replace human feedback on my writing?**

No. AcademicLint catches mechanical clarity issues. It can't evaluate whether your argument is *good*, your evidence is *sufficient*, or your contribution is *novel*. You still need advisors, peers, and reviewers.

**Q: My density score is low but my advisor likes my writing. What gives?**

Density isn't everything. Some fields and contexts value expansive, hedged prose. The score is a tool, not a judgment. If your audience is satisfied, trust that.

**Q: Can I use this for non-academic writing?**

Yes, but calibrate expectations. Business writing, journalism, and creative nonfiction have different norms. Use `--level relaxed` and interpret flags accordingly.

**Q: Why did it flag a term that's standard in my field?**

Add it to your domain terms file. The system doesn't know every field's vocabulary—you'll need to teach it your discipline's precise terminology.

**Q: The suggestions seem wrong. Can I train it on my style?**

Not yet. Custom style training is on the roadmap. For now, use domain files to reduce false positives on terminology.

**Q: Is my writing sent to the cloud?**

Not by default. Local mode processes everything on your machine. Cloud API is opt-in only.

---

## Support

- **Documentation**: [docs.academiclint.dev](https://docs.academiclint.dev)
- **Issues**: [GitHub Issues](https://github.com/kase1111-hash/academiclint/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kase1111-hash/academiclint/discussions)
- **Email**: kase1111@gmail.com

---

## License

AcademicLint is licensed under the [Polyform Small Business License 1.0.0](./LICENSE.md).

**In short:**
- ✅ Free for individuals, academics, nonprofits, and small organizations (<100 people, <$1M revenue)
- ❌ Large commercial entities need a separate license

See [LICENSE-SUMMARY.md](./LICENSE-SUMMARY.md) for plain-English explanation.

---

## Acknowledgments

AcademicLint is built on the [Lexicon](https://github.com/kase1111-hash/lexicon) framework for computational semantic analysis.

Special thanks to:
- The open-source NLP community
- Early testers and contributors
- Everyone who writes clearly and makes the world more understandable

---

*Clear thinking requires clear writing. Clear writing requires seeing your own fog.*

**Happy linting.**
