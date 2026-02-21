# AcademicLint Security Audit Report

**Date:** 2026-02-21
**Methodology:** [Agent-OS Repository Security Audit Checklist (Post-Moltbook Hardening Guide v1.0)](https://github.com/kase1111-hash/Claude-prompts/blob/main/Agentic-Security-Audit.md)
**Version Audited:** 0.1.0 (Alpha)
**Repository:** AcademicLint

---

## Executive Summary

This security audit evaluates AcademicLint against the three-tier Agent-OS Security Audit Checklist, adapted for a non-agentic Python CLI/library tool. The checklist was designed for AI agent repositories but its principles apply broadly to any software handling user input, executing subprocesses, and loading external configuration.

### Overall Security Posture: **GOOD — 5 findings requiring attention**

| Tier | Category | Status | Finding Count |
|------|----------|--------|---------------|
| 1 | Credential Storage | PASS | 0 |
| 1 | Default-Deny / Least Privilege | WARN | 2 |
| 1 | Configuration Path Security | PASS | 0 |
| 2 | Input Validation Gate | PASS | 0 |
| 2 | Outbound Secret Scanning | N/A | 0 |
| 2 | Subprocess Sandboxing | FAIL | 1 |
| 3 | Vibe-Code Review Gate (CI/CD) | PASS | 0 |
| 3 | Dependency Security | WARN | 1 |
| 3 | API Security | WARN | 1 |

**Critical:** 0 | **High:** 1 | **Medium:** 3 | **Low:** 1

---

## Quick-Scan Results

The following grep-based scans from the audit checklist were executed against the repository:

| Scan | Command Description | Result |
|------|-------------------|--------|
| Plaintext secrets | Hardcoded passwords/tokens/keys in source | **PASS** — No secrets found in source. Only test file `tests/test_security.py` contains dummy values for testing secret masking. |
| Hardcoded URL fetching (C2 indicators) | `requests.get`, `urllib`, `fetch`, `httpx` calls | **PASS** — No HTTP client calls found in any source file. |
| Unsandboxed shell execution | `subprocess.run`, `os.system`, `exec()`, `eval()` | **WARN** — 2 `subprocess.run` calls found (see Finding SEC-03). |
| Predictable config paths | `Path.home()`, `expanduser`, `~/` references | **INFO** — Uses `~/.cache/academiclint/` — standard XDG-style path. Acceptable. |
| Missing auth on endpoints | `0.0.0.0`, CORS `allow_all` patterns | **WARN** — Default API host binds to `0.0.0.0`, CORS origins empty in production config but wide-open in `.env.example` (see Finding SEC-04). |
| Dangerously committed files | `.pem`, `.key`, `.env`, `id_rsa` | **PASS** — `.gitignore` covers `.env`. No private keys or certificate files found in repository. |

---

## Tier 1: Immediate Wins (Architectural Defaults)

### 1.1 Credential Storage

**Status: PASS**

- No plaintext secrets exist in source code, configuration files, or git history.
- `.env.example` contains only placeholder/commented examples for `SENTRY_DSN`, `AWS_ACCESS_KEY_ID`, and `VAULT_TOKEN` — all properly commented out with instructional text.
- `.gitignore` correctly excludes `.env` files (line 54).
- `EnvConfig.to_dict()` (`src/academiclint/utils/env.py:398-411`) explicitly excludes the `sentry_dsn` property from serialization, preventing secret leakage in logs or debug output.
- `mask_secret()` (`src/academiclint/utils/env.py:306-323`) provides proper masking with configurable visible character count.

**Evidence:**
```
.gitignore:54 → .env
env.py:399   → def to_dict(self) -> dict[str, Any]:  # excludes sentry_dsn
env.py:306   → def mask_secret(value: str, visible_chars: int = 4) -> str:
```

### 1.2 Default-Deny Permissions / Least Privilege

**Status: WARN** (2 findings)

#### Finding SEC-01: Default API bind address is `0.0.0.0` (Medium)

**Files:**
- `config/default.yaml:34` — `host: "0.0.0.0"`
- `src/academiclint/utils/env.py:386` — `default="0.0.0.0"`
- `.env.example:68` — `ACADEMICLINT_API_HOST=0.0.0.0`

**Issue:** The default configuration binds the API server to all network interfaces. While the development config (`config/development.yaml:34`) correctly uses `127.0.0.1`, the production default in `config/default.yaml` uses `0.0.0.0`. Since `default.yaml` is the base configuration inherited by all environments, this means any deployment that doesn't explicitly override the host will expose the API to the network.

**Risk:** An unintentional network-exposed API without authentication or rate limiting.

**Recommendation:** Change `config/default.yaml` line 34 to `host: "127.0.0.1"`. Deployments that intentionally need network exposure can override this. The safe default should be restrictive.

#### Finding SEC-02: Empty CORS origins defaults to permissive behavior (Low)

**File:** `config/default.yaml:39` — `cors_origins: []`

**Issue:** An empty `cors_origins` list in the default config is ambiguous. Depending on the CORS middleware implementation (referenced in `AUDIT_REPORT.md:174` as `allow_origins=["*"]`), an empty list may be interpreted as "allow all origins" rather than "allow none."

**Note:** The API server code itself was not found in the repository (no `src/academiclint/api/` directory exists), suggesting it may be planned but not yet implemented. The OpenAPI spec at `docs/openapi.yaml` describes the API interface. When implemented, this should default to restrictive CORS.

**Recommendation:** When the API server is implemented, ensure empty `cors_origins` means "deny all" and require explicit configuration for allowed origins.

### 1.3 Configuration Path Security

**Status: PASS**

- Cache directory uses standard location: `~/.cache/academiclint/` (`src/academiclint/models/manager.py:11`, `src/academiclint/models/cache.py:11`)
- Config follows XDG conventions: `~/.config/academiclint/config.yml` (documented in `SPEC.md:1042`)
- No non-standard or surprising path locations.
- `_find_env_file()` in `env.py:78-92` limits directory traversal to 10 levels upward, preventing unbounded filesystem walking.

---

## Tier 2: Core Enforcement Layer

### 2.1 Input Classification / Validation Gate

**Status: PASS**

Input validation is comprehensive and well-implemented in `src/academiclint/utils/validation.py`:

| Control | Implementation | Location |
|---------|---------------|----------|
| Max text length | 10,000,000 chars | `validation.py:11` |
| Max file size | 50,000,000 bytes (50 MB) | `validation.py:12` |
| Null byte sanitization | `text.replace("\x00", "")` | `validation.py:51` |
| Line ending normalization | `\r\n` → `\n`, `\r` → `\n` | `validation.py:47` |
| File extension allowlist | `.md`, `.txt`, `.tex`, `.markdown`, `.text` only | `validation.py:15` |
| Path traversal protection | `path.resolve()` for canonical paths | `validation.py:86` |
| ReDoS prevention | Nested quantifier detection + pattern length limit (1000 chars) | `validation.py:156-193` |
| Type validation | Explicit type checks before processing | `validation.py:34-35` |

**Additional positive observations:**
- `Config.from_file()` uses `yaml.safe_load()` (`config.py:153`), preventing YAML deserialization attacks.
- `domains/loader.py:24` also uses `yaml.safe_load()`.
- `Config.__post_init__()` validates all configuration values with range and type checks (`config.py:63-128`).
- The existing `test_security.py` has 36 security-focused test cases covering injection, traversal, ReDoS, resource exhaustion, and information leakage.

### 2.2 Outbound Secret Scanning

**Status: N/A**

AcademicLint does not make outbound network requests in its core functionality. There are no HTTP client imports (`requests`, `httpx`, `urllib.request`) anywhere in the source code. The tool is a local text analysis library and CLI.

The only external communication is optional Sentry error reporting (configured but disabled by default in `config/default.yaml:49-53`). When enabled, Sentry SDKs have their own data scrubbing for sensitive values.

### 2.3 Subprocess Sandboxing

**Status: FAIL** (1 finding)

#### Finding SEC-03: Unsandboxed subprocess execution with user-influenced input (High)

**Files:**
- `src/academiclint/models/manager.py:58-63`
- `src/academiclint/cli/setup.py:51-55`

**Issue:** Both files execute subprocess commands to download spaCy models:

```python
# models/manager.py:58
result = subprocess.run(
    ["python", "-m", "spacy", "download", model_name],
    capture_output=True,
    text=True,
)

# cli/setup.py:51
result = subprocess.run(
    ["python", "-m", "spacy", "download", model],
    capture_output=True,
    text=True,
)
```

The `model_name`/`model` parameter originates from:
1. `ModelManager.download_model(model_name)` — called with values from `DEFAULT_MODELS` list or user-provided names
2. `cli/setup.py` — the `--models` CLI option accepts arbitrary comma-separated strings from the user

While the use of list-form `subprocess.run()` (not `shell=True`) prevents shell injection, the `model_name` string is passed directly to `spacy download` without validation. A malicious model name could potentially exploit spaCy's download mechanism or pip's package resolution.

**Specific risks:**
- No validation that `model_name` matches expected spaCy model naming patterns
- The `setup.py:25` check `if model.startswith("en_core_web")` provides a partial guard in the CLI path, but `ModelManager.download_model()` at `manager.py:49` has the same check — other callers could bypass it
- No `timeout` parameter on either `subprocess.run()` call, meaning a hanging download could block indefinitely

**Recommendation:**
1. Add a strict allowlist or regex validation for model names before passing to subprocess (e.g., `re.match(r'^[a-z]{2}_core_web_(sm|md|lg|trf)$', model_name)`)
2. Add a `timeout` parameter to both `subprocess.run()` calls (e.g., `timeout=300`)
3. Consider using `spacy.cli.download()` Python API instead of shelling out, which avoids subprocess entirely

### 2.4 YAML Deserialization Safety

**Status: PASS**

All YAML loading uses `yaml.safe_load()`:
- `src/academiclint/core/config.py:153` — config file loading
- `src/academiclint/domains/loader.py:24` — domain file loading

The `test_security.py:491-505` test case explicitly verifies that `!!python/object` YAML tags are rejected, confirming protection against arbitrary code execution via YAML deserialization.

---

## Tier 3: Protocol-Level Maturity

### 3.1 Vibe-Code Security Review Gate (CI/CD)

**Status: PASS**

The CI/CD pipeline includes multiple security layers:

| Gate | Tool | Location |
|------|------|----------|
| Static security analysis | Bandit | `.github/workflows/ci.yml:79-96` |
| Linting (includes flake8-bandit rules) | Ruff with `S` rules | `pyproject.toml:114` |
| Type checking | mypy (strict mode) | `.github/workflows/ci.yml:57-74` |
| Pre-commit security hooks | Bandit pre-commit | `.pre-commit-config.yaml:41-46` |
| Release quality gates | Full test + security scan before publish | `.github/workflows/release.yml:31-67` |

**Positive observations:**
- Release pipeline (`release.yml`) requires quality checks to pass before publishing
- PyPI publishing uses OIDC trusted publishing (`id-token: write`) instead of long-lived API tokens
- Pre-commit hooks catch security issues before they reach CI
- Bandit is configured with reasonable skip rules (only `B101` for asserts and `B104` for dev server bind)

### 3.2 Dependency Security

**Status: WARN** (1 finding)

#### Finding SEC-04: No automated dependency vulnerability scanning in CI (Medium)

**File:** `pyproject.toml:44-55`, `.github/workflows/ci.yml`

**Issue:** While `safety` is listed as a dev dependency (`pyproject.toml:53`), it is never executed in the CI pipeline. The CI runs `bandit` for static analysis of the project's own code, but there is no step that checks dependencies for known vulnerabilities.

**Current dependencies:**
- `spacy>=3.7.0,<4.0.0` — Large NLP library with many transitive dependencies
- `click>=8.0.0` — CLI framework
- `pyyaml>=6.0` — YAML parser
- `rich>=13.0.0` — Terminal formatting
- `pydantic>=2.0.0` — Data validation

spaCy in particular pulls in a large dependency tree (numpy, thinc, cymem, etc.) that should be monitored for vulnerabilities.

**Recommendation:**
1. Add a `safety check` or `pip-audit` step to `.github/workflows/ci.yml`
2. Consider using GitHub's Dependabot or similar for automated dependency update PRs
3. Pin transitive dependency versions in a lockfile for reproducible builds

### 3.3 API Security Posture

**Status: WARN** (1 finding)

#### Finding SEC-05: API design lacks authentication and rate limiting (Medium)

**Files:**
- `docs/openapi.yaml:30-37` — Explicitly documents "no authentication" and "no rate limiting"
- `config/default.yaml:32-39` — API configuration section

**Issue:** The OpenAPI specification explicitly states:

> "Currently, the API does not require authentication. For production deployments, consider adding API key authentication via a reverse proxy."
> "No rate limiting is enforced by default. Configure rate limiting at the infrastructure level for production use."

While the API server is not yet implemented (no `src/academiclint/api/` directory), the architecture documentation establishes a pattern of delegating security to infrastructure. This is acceptable for an alpha-stage project, but these should be addressed before any production deployment.

**Risk:** Without authentication, anyone with network access can submit text for analysis. Without rate limiting, the service is vulnerable to resource exhaustion (spaCy model processing is CPU-intensive).

**Recommendation:**
1. Implement API key authentication before any production deployment
2. Add rate limiting middleware (e.g., `slowapi` for FastAPI)
3. Document these as explicit pre-production requirements, not just suggestions

---

## Findings Summary

| ID | Severity | Title | Tier | Status |
|----|----------|-------|------|--------|
| SEC-01 | Medium | Default API bind to `0.0.0.0` | 1 | Open |
| SEC-02 | Low | Ambiguous empty CORS origins default | 1 | Open |
| SEC-03 | High | Unsandboxed subprocess with user input | 2 | Open |
| SEC-04 | Medium | No dependency vulnerability scanning in CI | 3 | Open |
| SEC-05 | Medium | API lacks authentication and rate limiting | 3 | Open |

---

## Positive Security Observations

The following security practices are well-implemented and deserve recognition:

1. **Comprehensive input validation** — `validation.py` handles null bytes, path traversal, file size limits, text length limits, extension allowlisting, and ReDoS prevention.
2. **Safe YAML loading** — All YAML parsing uses `yaml.safe_load()`, with test verification.
3. **Secret masking** — `mask_secret()` utility prevents accidental secret exposure in logs.
4. **Config serialization excludes secrets** — `EnvConfig.to_dict()` omits `sentry_dsn`.
5. **No network calls in core library** — The text analysis pipeline is fully offline.
6. **Well-structured exception hierarchy** — Custom exceptions prevent stack trace leakage to end users.
7. **Non-predictable result IDs** — Uses `uuid.uuid4()` for analysis result identifiers.
8. **Security test suite** — 36 dedicated security tests covering injection, traversal, DoS, and information leakage.
9. **OIDC-based PyPI publishing** — Release pipeline uses trusted publishing, not long-lived API tokens.
10. **Pre-commit security hooks** — Bandit runs on every commit via pre-commit framework.

---

## Checklist Items Not Applicable

The following audit checklist categories from the Agentic Security Audit are not applicable to AcademicLint, as it is not an AI agent system:

| Checklist Item | Reason Not Applicable |
|----------------|----------------------|
| Cryptographic Agent Identity (1.3) | Not an agent; no inter-process identity needed |
| Memory Integrity and Provenance (2.2) | No persistent memory or conversation state |
| Outbound Secret Scanning (2.3) | No outbound network communication |
| Skill/Module Signing (2.4) | No dynamic skill/plugin loading from untrusted sources |
| Constitutional Audit Trail (3.1) | Not an autonomous agent; no decision chain to log |
| Mutual Agent Authentication (3.2) | No agent-to-agent communication |
| Anti-C2 Pattern Enforcement (3.3) | No periodic fetch-and-execute patterns |
| Agent Coordination Boundaries (3.5) | No multi-agent coordination |

---

## Remediation Priority

### Immediate (before any public API deployment)
1. **SEC-03:** Validate subprocess model name inputs with strict allowlist
2. **SEC-01:** Change default API host from `0.0.0.0` to `127.0.0.1`

### Before Production
3. **SEC-05:** Implement API authentication and rate limiting
4. **SEC-04:** Add `pip-audit` or `safety` step to CI pipeline

### Best Practice
5. **SEC-02:** Ensure CORS middleware treats empty origins as deny-all

---

*End of Security Audit Report*
