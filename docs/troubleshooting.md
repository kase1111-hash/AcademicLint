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

3. **Reduce batch size:**
   ```yaml
   # .academiclint.yml
   performance:
     batch_size: 1000  # Default is 5000
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

3. **Disable unnecessary detectors:**
   ```yaml
   # .academiclint.yml
   disabled_rules:
     - JARGON_DENSE  # Expensive computation
   ```

4. **Use API for large documents:**
   ```bash
   academiclint serve &
   curl -X POST http://localhost:8080/v1/check -d '{"text": "..."}'
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

2. **Adjust memory limits:**
   ```yaml
   # .academiclint.yml
   performance:
     max_memory_mb: 2048
   ```

### CPU usage at 100%

This is normal during analysis. AcademicLint uses all available cores. To limit:

```yaml
# .academiclint.yml
performance:
  max_workers: 2  # Limit parallel processing
```

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

4. **Disable specific rules:**
   ```yaml
   # .academiclint.yml
   disabled_rules:
     - WEASEL
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

3. **Ensure all detectors enabled:**
   ```yaml
   # .academiclint.yml
   disabled_rules: []  # Empty = all enabled
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

2. **Configure LaTeX handling:**
   ```yaml
   # .academiclint.yml
   latex:
     ignore_math: true
     ignore_commands:
       - cite
       - ref
   ```

---

## Integration Problems

### VS Code extension not working

**Solutions:**

1. **Verify installation:**
   - Open VS Code Extensions panel
   - Search for "AcademicLint"
   - Ensure it's installed and enabled

2. **Check output panel:**
   - View → Output → Select "AcademicLint"
   - Look for error messages

3. **Verify CLI works:**
   ```bash
   academiclint --version
   ```

4. **Reload VS Code:**
   - Command Palette (Ctrl/Cmd + Shift + P)
   - "Developer: Reload Window"

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

## API Issues

### "Connection refused"

**Symptom:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Solutions:**

1. **Start the server:**
   ```bash
   academiclint serve --port 8080
   ```

2. **Check port availability:**
   ```bash
   lsof -i :8080  # Linux/macOS
   netstat -an | findstr 8080  # Windows
   ```

3. **Use correct URL:**
   ```
   http://localhost:8080/v1/check  # Not https
   ```

### "401 Unauthorized"

**Symptom:**
```json
{"error": "Invalid or missing API key"}
```

**Solutions:**

1. **Set API key:**
   ```bash
   export ACADEMICLINT_API_KEY=your_key
   ```

2. **Include in request:**
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" ...
   ```

### "413 Request Entity Too Large"

**Symptom:**
```json
{"error": "Request body too large"}
```

**Solution:**
The default limit is 1MB. For larger texts:

1. **Split into chunks**
2. **Increase limit (self-hosted):**
   ```bash
   academiclint serve --max-body-size 10485760  # 10MB
   ```

### Rate limiting

**Symptom:**
```json
{"error": "Rate limit exceeded", "retry_after": 60}
```

**Solutions:**

1. **Wait and retry:**
   ```python
   import time
   time.sleep(response.headers['Retry-After'])
   ```

2. **Batch requests:**
   ```python
   # Instead of many small requests
   texts = ["...", "...", "..."]
   result = client.check_batch(texts)
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

- **Documentation:** [docs.academiclint.dev](https://docs.academiclint.dev)
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
| VS Code not working | Reload window |
| API unauthorized | Check API key in header |

---

*If your issue isn't covered here, please [open a GitHub issue](https://github.com/kase1111-hash/academiclint/issues/new).*
