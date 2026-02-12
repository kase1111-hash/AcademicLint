# Troubleshooting Guide

This guide covers common issues and their solutions when using AcademicLint.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Runtime Errors](#runtime-errors)
3. [Performance Problems](#performance-problems)
4. [Analysis Issues](#analysis-issues)
5. [Integration Problems](#integration-problems)
6. [API Issues](#api-issues)
7. [Configuration Problems](#configuration-problems)
8. [Getting Help](#getting-help)

---

## Installation Issues

### "Python version not supported"

**Symptom:**
```
ERROR: academiclint requires Python 3.11+, but you have 3.9.x
```

**Solution:**
Install Python 3.11 or later:

```bash
# macOS (Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11

# Windows
# Download from python.org

# Then install with specific version
python3.11 -m pip install academiclint
```

### "Permission denied" during installation

**Symptom:**
```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```

**Solutions:**

1. **Use user installation:**
   ```bash
   pip install --user academiclint
   ```

2. **Use pipx (recommended):**
   ```bash
   pip install pipx
   pipx install academiclint
   ```

3. **Use a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate     # Windows
   pip install academiclint
   ```

### "No space left on device"

**Symptom:**
```
ERROR: No space left on device
```

**Solution:**
AcademicLint requires ~2GB for models. Free up space or specify alternative cache location:

```bash
export ACADEMICLINT_CACHE_DIR=/path/with/space
academiclint setup
```

### "Could not find a version that satisfies the requirement"

**Symptom:**
```
ERROR: Could not find a version that satisfies the requirement academiclint
```

**Solutions:**

1. **Upgrade pip:**
   ```bash
   pip install --upgrade pip
   ```

2. **Check Python version:**
   ```bash
   python --version  # Must be 3.11+
   ```

3. **Try a different index:**
   ```bash
   pip install --index-url https://pypi.org/simple/ academiclint
   ```

---

## Runtime Errors

### "Model not found"

**Symptom:**
```
ERROR: Required model 'semantic-analyzer-v1' not found
```

**Solution:**
Download models manually:

```bash
academiclint setup
```

If that fails, try:
```bash
academiclint setup --force  # Re-download all models
```

### "Out of memory"

**Symptom:**
```
MemoryError: Unable to allocate memory
```

**Solutions:**

1. **Close other applications** to free RAM

2. **Analyze in chunks:**
   ```bash
   academiclint check paper.md --sections "introduction"
   academiclint check paper.md --sections "methods"
   ```

### "spaCy model not found"

**Symptom:**
```
OSError: [E050] Can't find model 'en_core_web_lg'
```

**Solution:**
```bash
python -m spacy download en_core_web_lg
```

### "Import error" or "Module not found"

**Symptom:**
```
ModuleNotFoundError: No module named 'academiclint'
```

**Solutions:**

1. **Verify installation:**
   ```bash
   pip show academiclint
   ```

2. **Check PATH:**
   ```bash
   which academiclint  # Linux/macOS
   where academiclint  # Windows
   ```

3. **Reinstall:**
   ```bash
   pip uninstall academiclint
   pip install academiclint
   ```

---

## Performance Problems

### Analysis is very slow

**Possible causes and solutions:**

1. **First-time initialization:**
   - First run loads models into memory (~30s)
   - Subsequent runs are faster

2. **Large files:**
   ```bash
   # Analyze specific sections
   academiclint check paper.md --sections "introduction,conclusion"

   # Use relaxed mode for faster analysis
   academiclint check paper.md --level relaxed
   ```

3. **Use a lower strictness level:**
   ```bash
   academiclint check paper.md --level relaxed
   ```

### High memory usage

**Solutions:**

1. **Process files sequentially:**
   ```bash
   # Instead of
   academiclint check *.md

   # Do
   for f in *.md; do academiclint check "$f"; done
   ```

### CPU usage at 100%

This is normal during analysis. NLP processing is CPU-intensive. Analyzing smaller sections can help reduce load.

---

## Analysis Issues

### Too many false positives

**Solutions:**

1. **Use appropriate strictness:**
   ```bash
   academiclint check paper.md --level relaxed
   ```

2. **Add domain vocabulary:**
   ```yaml
   # .academiclint.yml
   domain_terms:
     - your_technical_term
     - another_term
   ```

3. **Use a domain preset:**
   ```bash
   academiclint check paper.md --domain philosophy
   ```

### Not catching obvious issues

**Solutions:**

1. **Increase strictness:**
   ```bash
   academiclint check paper.md --level strict
   ```

2. **Lower density threshold:**
   ```yaml
   # .academiclint.yml
   min_density: 0.40
   ```

3. **Verify models are installed:**
   ```bash
   academiclint setup
   ```

### Incorrect line numbers

**Possible causes:**

1. **Encoding issues:**
   ```bash
   # Convert to UTF-8
   iconv -f ISO-8859-1 -t UTF-8 paper.md > paper_utf8.md
   ```

2. **Mixed line endings:**
   ```bash
   # Normalize line endings (Linux/macOS)
   sed -i 's/\r$//' paper.md
   ```

### LaTeX not parsing correctly

**Solutions:**

1. **Use plain text extraction:**
   ```bash
   # Convert LaTeX to text first
   detex paper.tex > paper.txt
   academiclint check paper.txt
   ```

2. **Use ignore patterns for LaTeX-specific content:**
   ```yaml
   # .academiclint.yml
   ignore_patterns:
     - "^\\\\begin"
     - "^\\\\end"
   ```

---

## Integration Problems

### GitHub Actions failing

**Common issues:**

1. **Python version:**
   ```yaml
   - uses: actions/setup-python@v5
     with:
       python-version: '3.11'  # Must be 3.11+
   ```

2. **Caching models:**
   ```yaml
   - uses: actions/cache@v3
     with:
       path: ~/.cache/academiclint
       key: academiclint-models-v1

   - run: academiclint setup
   ```

3. **Exit code handling:**
   ```yaml
   - run: academiclint check docs/ --fail-under 0.40
     continue-on-error: false  # Fail build on low density
   ```

### Pre-commit hook slow

**Solutions:**

1. **Run only on changed files:**
   ```yaml
   # .pre-commit-config.yaml
   - id: academiclint
     stages: [commit]  # Not on push
   ```

2. **Use relaxed mode:**
   ```yaml
   args: ['--level', 'relaxed']
   ```

3. **Skip in CI:**
   ```bash
   SKIP=academiclint git commit -m "Quick fix"
   ```

---

## Configuration Problems

### Configuration file not found

**Symptom:**
```
WARNING: No configuration file found, using defaults
```

**Solutions:**

1. **Verify file location:**
   - `.academiclint.yml` in project root
   - Or `~/.config/academiclint/config.yml` for global

2. **Check file name:**
   - Must be `.academiclint.yml` (note leading dot)
   - Or `academiclint.yml` (without dot)

3. **Specify explicitly:**
   ```bash
   academiclint check paper.md --config /path/to/config.yml
   ```

### Invalid configuration

**Symptom:**
```
ERROR: Invalid configuration: 'levl' is not a valid option
```

**Solution:**
Check for typos. Valid options:

```yaml
level: standard           # not "levl"
min_density: 0.50        # not "minimum_density"
domain_terms: []         # not "domain-terms"
```

### Configuration not taking effect

**Solutions:**

1. **Check precedence:**
   - CLI args override config file
   - Project config overrides global config

2. **Verify YAML syntax:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('.academiclint.yml'))"
   ```

3. **Use verbose mode:**
   ```bash
   academiclint check paper.md -v  # Shows loaded config
   ```

---

## Getting Help

### Before asking for help

1. **Check the version:**
   ```bash
   academiclint --version
   ```

2. **Enable debug logging:**
   ```bash
   academiclint check paper.md --debug
   ```

3. **Search existing issues:**
   - [GitHub Issues](https://github.com/kase1111-hash/academiclint/issues)

### How to report a bug

Include:
- AcademicLint version
- Python version
- Operating system
- Full error message
- Minimal reproduction steps

```bash
# Generate system info
academiclint --debug --version
python --version
```

### Getting support

- **Documentation:** See the [`docs/`](.) directory
- **GitHub Issues:** [Report bugs](https://github.com/kase1111-hash/academiclint/issues)
- **Discussions:** [Ask questions](https://github.com/kase1111-hash/academiclint/discussions)
- **Email:** kase1111@gmail.com

---

## Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Model not found | `academiclint setup` |
| Permission denied | `pip install --user academiclint` |
| Too slow | `--level relaxed` or `--sections` |
| Too many flags | Add terms to `domain_terms` |
| Not enough flags | `--level strict` |
| Memory error | Analyze in sections |
| spaCy model missing | `python -m spacy download en_core_web_lg` |

---

*If your issue isn't covered here, please [open a GitHub issue](https://github.com/kase1111-hash/academiclint/issues/new).*
