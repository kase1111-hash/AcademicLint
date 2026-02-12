# Frequently Asked Questions

A comprehensive FAQ for AcademicLint covering installation, usage, interpretation, and troubleshooting.

---

## Table of Contents

1. [General Questions](#general-questions)
2. [Installation & Setup](#installation--setup)
3. [Usage & Configuration](#usage--configuration)
4. [Understanding Results](#understanding-results)
5. [Domain Customization](#domain-customization)
6. [Integrations](#integrations)
7. [Privacy & Security](#privacy--security)
8. [Licensing](#licensing)
9. [Troubleshooting](#troubleshooting)

---

## General Questions

### What is AcademicLint?

AcademicLint is a semantic clarity analyzer for academic writing. Unlike grammar checkers (Grammarly, LanguageTool), it identifies conceptual issues: vague terms, unsupported claims, circular definitions, and low-density prose. It answers the question "What do you actually mean?" rather than "Is this grammatically correct?"

### How is this different from Grammarly or other writing tools?

| Tool | Focuses On |
|------|------------|
| Grammarly | Grammar, spelling, punctuation, style |
| LanguageTool | Grammar, spelling, style rules |
| Hemingway | Readability, sentence complexity |
| **AcademicLint** | **Semantic clarity, logical structure, specificity** |

AcademicLint catches issues other tools miss:
- "Many experts believe..." (Who? Cite them.)
- "Society has changed..." (Which society? How?)
- "X causes Y" (What's the mechanism?)

### Who is this for?

- **Students** writing papers, theses, dissertations
- **Researchers** preparing manuscripts for publication
- **Academics** reviewing drafts
- **Technical writers** creating documentation
- **Anyone** who wants to write more precisely

### Is this going to replace human feedback?

No. AcademicLint catches mechanical clarity issues. It cannot evaluate whether your argument is *good*, your evidence is *sufficient*, or your contribution is *novel*. You still need advisors, peers, and reviewers.

### Can I use this for non-academic writing?

Yes, but calibrate expectations. Business writing, journalism, and creative nonfiction have different norms. Use `--level relaxed` and interpret flags accordingly. Some "vagueness" is intentional in non-academic contexts.

---

## Installation & Setup

### What are the system requirements?

- **Python:** 3.11 or higher
- **Disk space:** ~2GB (for language models)
- **RAM:** 4GB minimum, 8GB recommended
- **OS:** Linux, macOS, Windows 10+

### How do I install AcademicLint?

```bash
# Via pip
pip install academiclint

# Via pipx (recommended for CLI tools)
pipx install academiclint

# From source
git clone https://github.com/kase1111-hash/academiclint.git
cd academiclint
pip install -e .
```

### Why does the first run take so long?

On first run, AcademicLint downloads language models (~1.5GB). This only happens once. Subsequent runs start immediately.

To pre-download models:
```bash
academiclint setup
```

### Can I use AcademicLint offline?

Yes. After the initial model download, AcademicLint runs entirely offline. All processing happens locally on your machine — no network connection is required after setup.

```bash
# Download models once
academiclint setup

# Then use normally — no internet needed
academiclint check paper.md
```

### How do I verify the installation?

```bash
academiclint --version
academiclint check --help
```

---

## Usage & Configuration

### What file formats are supported?

| Format | Extension | Support |
|--------|-----------|---------|
| Plain text | `.txt` | ✅ Full |
| Markdown | `.md` | ✅ Full |
| LaTeX | `.tex` | ✅ Full (math ignored) |

### How do I analyze a file?

```bash
# Basic usage
academiclint check paper.md

# With strictness level
academiclint check paper.md --level strict

# Output as JSON
academiclint check paper.md --format json

# Analyze specific sections
academiclint check paper.md --sections "introduction,conclusion"
```

### What strictness levels are available?

| Level | Use Case | Density Threshold |
|-------|----------|-------------------|
| `relaxed` | Blog posts, informal | 0.30 |
| `standard` | Coursework, general | 0.50 |
| `strict` | Thesis, journal | 0.65 |
| `academic` | Peer review prep | 0.75 |

### How do I configure AcademicLint?

Create `.academiclint.yml` in your project root:

```yaml
level: standard
min_density: 0.50

domain_terms:
  - epistemology
  - hermeneutics

ignore_patterns:
  - "Abstract:"
  - "References"

output:
  format: terminal
  show_suggestions: true
```

### Can I ignore specific rules or flags?

You can reduce false positives by adjusting the strictness level or adding domain-specific terms:

```yaml
# .academiclint.yml
level: relaxed                 # Less aggressive flagging
domain_terms:
  - your_technical_term        # Won't be flagged as jargon
```

Or use a built-in domain:
```bash
academiclint check paper.md --domain philosophy
```

### How do I analyze text from stdin?

```bash
cat paper.md | academiclint check -
echo "Some text" | academiclint check -
```

---

## Understanding Results

### What does the density score mean?

Semantic density (0.0-1.0) measures information content vs. filler:

| Score | Grade | Interpretation |
|-------|-------|----------------|
| 0.0-0.2 | Vapor | Almost no content |
| 0.2-0.4 | Thin | Significant filler |
| 0.4-0.6 | Adequate | Room for improvement |
| 0.6-0.8 | Dense | Clear writing |
| 0.8-1.0 | Crystalline | Exceptionally precise |

Academic writing should generally target 0.5-0.7.

### Is higher density always better?

No. A score above 0.9 can indicate writing that's too compressed for readability. Dense technical writing needs breathing room. Context matters.

### My density score is low but my advisor likes my writing. What gives?

Density isn't everything. Some fields and contexts value expansive, hedged prose. The score is a tool, not a judgment. If your audience is satisfied, trust that.

### What do the different flag types mean?

| Flag | Meaning |
|------|---------|
| `UNDERSPECIFIED` | Term lacks clear referent or scope |
| `UNSUPPORTED_CAUSAL` | Causal claim without mechanism/evidence |
| `CIRCULAR` | Definition that restates rather than clarifies |
| `WEASEL` | Attribution avoiding accountability |
| `HEDGE_STACK` | Excessive hedging evacuating meaning |
| `JARGON_DENSE` | Technical terms without explanation |
| `CITATION_NEEDED` | Factual claim requiring source |
| `FILLER` | Empty phrase adding no information |

### Why did it flag a term that's standard in my field?

The system doesn't know every field's vocabulary. Add it to your domain terms:

```yaml
# .academiclint.yml
domain_terms:
  - your_term_here
```

Or use a built-in domain:
```bash
academiclint check paper.md --domain philosophy
```

### When should I ignore flags?

Flags are suggestions, not commands. Ignore when:
- **Intentional ambiguity** — Sometimes vagueness is the point
- **Audience calibration** — Technical terms are fine for experts
- **Stylistic choice** — Some hedging is appropriate caution
- **False positives** — No system is perfect

---

## Domain Customization

### What domains are built-in?

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

### How do I use a built-in domain?

```bash
academiclint check paper.md --domain philosophy
```

### How do I create a custom domain?

Create a YAML file:

```yaml
# my-domain.yml
name: "Cognitive Science"
parent: psychology  # Inherit from built-in

technical_terms:
  - affordance
  - embodied cognition
  - enactivism

domain_weasels:
  - "the brain wants"
  - "evolved to"

density_baseline: 0.55
```

Use it:
```bash
academiclint check paper.md --domain-file my-domain.yml
```

### Can I combine multiple domains?

Not directly, but you can create a custom domain that inherits from one and adds terms from another:

```yaml
name: "Interdisciplinary"
parent: psychology

technical_terms:
  # Philosophy terms
  - epistemology
  - phenomenology
  # CS terms
  - algorithm
  - heuristic
```

---

## Integrations

### How do I use AcademicLint in VS Code?

A VS Code extension is planned for a future release (v0.2). In the meantime, you can run AcademicLint from the VS Code integrated terminal:

```bash
academiclint check paper.md
```

### How do I use AcademicLint in CI/CD?

Add to your GitHub Actions workflow:

```yaml
- name: AcademicLint Check
  run: |
    pip install academiclint
    academiclint check docs/ --format github --fail-under 0.40
```

### How do I use AcademicLint as a pre-commit hook?

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/kase1111-hash/academiclint
    rev: v0.1.0
    hooks:
      - id: academiclint
        args: ['--level', 'standard', '--fail-under', '0.40']
        types: [markdown]
```

### Is there a REST API?

A REST API server is planned for a future release (v0.2). Currently, you can use the Python library for programmatic access:

```python
from academiclint import Linter

linter = Linter()
result = linter.check("Your text here...")
print(f"Density: {result.density}")
```

---

## Privacy & Security

### Is my writing sent to the cloud?

**No**, by default. Local mode processes everything on your machine. Cloud API is opt-in only.

### What data does the API mode collect?

See our [Privacy Policy](../PRIVACY.md) for details. In short:
- Text processed in memory, immediately discarded
- No text stored
- No training on user data
- Minimal logging (no text content)

### Is AcademicLint GDPR compliant?

Yes. AcademicLint runs entirely on your local machine — no data is sent anywhere. All processing is local.

---

## Licensing

### Is AcademicLint free?

**Free for:**
- Individuals (personal use)
- Academics and researchers
- Nonprofits and educational institutions
- Small businesses (<100 people, <$1M revenue)

**Requires commercial license for:**
- Large organizations (≥100 people OR ≥$1M revenue)

### What license does AcademicLint use?

[PolyForm Small Business License 1.0.0](../LICENSE.md)

See [LICENSE-SUMMARY.md](../LICENSE-SUMMARY.md) for plain-English explanation.

### How do I get a commercial license?

Contact kase1111@gmail.com for commercial licensing inquiries.

---

## Troubleshooting

For detailed troubleshooting, see the [Troubleshooting Guide](./troubleshooting.md).

### Common Issues

**"Model not found" error:**
```bash
academiclint setup  # Download models
```

**"Permission denied" error:**
```bash
pip install --user academiclint
# Or use pipx
```

**Slow performance:**
- Ensure models are cached locally
- Use `--sections` to analyze specific parts
- Consider the API for large documents

**False positives:**
- Add terms to domain vocabulary
- Use appropriate strictness level
- Report persistent issues on GitHub

---

## Still Have Questions?

- **Documentation:** See the [`docs/`](.) directory
- **GitHub Issues:** [Report a bug or request a feature](https://github.com/kase1111-hash/academiclint/issues)
- **Discussions:** [Ask questions and share ideas](https://github.com/kase1111-hash/academiclint/discussions)
- **Email:** kase1111@gmail.com
