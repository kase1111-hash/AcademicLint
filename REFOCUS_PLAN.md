## REFOCUS PLAN: AcademicLint

**Goal:** Invert the infrastructure-to-logic ratio. Cut ~1,546 lines of unused ops code, defer ~1,042 lines of premature infrastructure, and reinvest effort into making the 8 detectors genuinely useful by leveraging the spaCy NLP pipeline that's already loaded but unused.

---

### PHASE 1: CUT (Remove dead weight)

**Estimated removal: ~1,546 lines across 5 files + scattered references**

These modules have zero active callers in the core linting logic. They are imported only by `__init__.py` re-exports.

| # | Action | File | Lines | Rationale |
|---|--------|------|-------|-----------|
| 1.1 | Delete | `src/academiclint/utils/metrics.py` | 529 | Full Prometheus-compatible metrics registry (Counter, Gauge, Histogram, Timer, export formats). No callers in any detector, formatter, or linter code. Replace with `time.perf_counter()` where timing is needed (already done in `linter.py:94`). |
| 1.2 | Delete | `src/academiclint/utils/error_reporting.py` | 404 | Sentry integration, StructuredLogger, JSONFormatter, ELK-compatible output. Zero callers. Standard `logging` module (already used throughout) is sufficient. |
| 1.3 | Delete | `src/academiclint/core/environments.py` | 474 | 8 nested dataclasses, 4-env-var detection chain, deep merge, env var expansion. Not used by `Config`, `Linter`, or any detector. The existing `Config.from_env()` and `Config.from_file()` already handle configuration. |
| 1.4 | Delete | `config/staging.yaml` | 67 | No staging environment exists. |
| 1.5 | Delete | `config/production.yaml` | 72 | No production deployment exists. References Sentry DSN, rate limiting, worker counts -- none of which are wired to code. |
| 1.6 | Clean up | `src/academiclint/utils/__init__.py` | - | Remove re-exports of deleted modules. |
| 1.7 | Clean up | `src/academiclint/core/__init__.py` | - | Remove re-exports of `environments`. |
| 1.8 | Clean up | `src/academiclint/__init__.py` | - | Remove any re-exports from deleted modules. |
| 1.9 | Clean up | `pyproject.toml:49-52` | - | Remove `sentence-transformers` and `torch` from optional dependencies. Not imported anywhere in source. |
| 1.10 | Clean up | `pyproject.toml:60-61` | - | Remove `bandit` and `safety` from dev dependencies if they aren't actively running in CI (verify first). |
| 1.11 | Delete | `src/academiclint/core/environments.py` tests | - | Remove `tests/test_env.py` (428 lines) which tests the deleted module. |
| 1.12 | Fix | `src/academiclint/core/linter.py:292-308` | - | Remove `check_stream()` method. It claims streaming but calls `self.check(text)` first. Misleading API surface. If true streaming is desired later, implement it properly by processing paragraphs incrementally through the NLP pipeline. |

**Verification:** After cuts, run `pytest` to confirm no breakage. The deleted modules have no active callers in core logic, so tests covering actual linting behavior should pass unchanged.

---

### PHASE 2: DEFER (Move out of v0.1 scope)

**Not deleting -- moving to a `deferred/` branch or feature-flagging behind actual need.**

| # | Action | Component | Lines | Rationale |
|---|--------|-----------|-------|-----------|
| 2.1 | Move to optional | `src/academiclint/api/` | 597 | REST API has no consumer yet. Keep the Python library and CLI as primary interfaces. Restore when an integration (VS Code extension, web UI) needs it. |
| 2.2 | Move to optional | `Dockerfile`, `docker-compose.yml` | 260 | Docker deployment depends on the API. Defer together. |
| 2.3 | Defer | `src/academiclint/formatters/html.py` | 185 | Terminal, JSON, and GitHub formatters cover the primary use cases (CLI users, programmatic consumers, CI pipelines). HTML can return when there's a web UI. |
| 2.4 | Trim | `src/academiclint/domains/manager.py` | - | Remove the 8 phantom domains from `BUILTIN_DOMAINS`. Keep only `philosophy` and `computer-science` which have actual `.yml` files. Advertising 10 domains when 8 return empty dicts is worse than advertising 2 real ones. |

---

### PHASE 3: DOUBLE DOWN (Make the detectors smart)

This is the core investment. Currently, all 8 detectors use regex against word lists. spaCy is loaded (600MB model) but only used for tokenization and sentence segmentation. Zero usage of `.dep_`, `.similarity`, `.vector`, `.children`, `.ancestors`, or `.head`.

#### 3.1 — VaguenessDetector: Add context awareness

**File:** `src/academiclint/detectors/vagueness.py`
**Problem:** Flags every occurrence of "this", "that", "these", "those", "area", "change", etc. These are perfectly clear in most contexts ("this paper argues...", "that result suggests...").
**Fix:**
- Use spaCy's dependency parsing to check if demonstrative pronouns ("this", "that") have a clear nominal referent (check if the token has a `det` dependency relation to a noun).
- If `token.dep_ == "det"` and the head is a specific noun, suppress the flag.
- If `token.dep_ == "nsubj"` with no nearby antecedent (standalone "this" as subject), flag it.
- Remove common false-positive triggers: "this paper", "that study", "these results", "those findings" -- demonstratives attached to concrete nouns are not vague.
- Reduce `VAGUE_TERMS` from 71 entries to a curated ~30 that are genuinely vague in most contexts (drop "change", "relate", "concern", "element", "individual").

**Acceptance test:** Run against 5 real abstracts from arxiv. False positive rate for demonstrative pronouns should drop below 20% (from estimated >80% currently).

#### 3.2 — CircularDetector: Use spaCy's lemmatizer

**File:** `src/academiclint/detectors/circular.py`
**Problem:** `_get_root()` (lines 95-104) is a hand-rolled suffix stripper that will miss non-obvious circularity and produce false matches.
**Fix:**
- Replace `_get_root()` with spaCy's `token.lemma_` which is already computed and available via `ProcessedDocument._spacy_doc`.
- Pass the spaCy doc through to the detector (it's already stored as `_spacy_doc` on `ProcessedDocument`).
- Compare lemmas instead of stripped stems: `token.lemma_ == defined_term.lemma_`.
- Add morphological awareness: "free" and "freedom" share a root via `token.morph` analysis.

**Acceptance test:** "Freedom is the state of being liberated" should NOT be flagged (different lemma). "Freedom is the state of being free" SHOULD be flagged. "Management is the organized handling of resources" should NOT be flagged.

#### 3.3 — CausalDetector: Add dependency structure analysis

**File:** `src/academiclint/detectors/causal.py`
**Problem:** Matches any sentence containing "caused", "lead to", "result in" etc. regardless of context. "The experiment was designed to test whether X causes Y (Smith, 2023)" would be flagged even though it's hedged and cited.
**Fix:**
- After regex match, use spaCy dependency parsing to extract the actual subject and object of the causal verb.
- Check for hedging modifiers on the causal verb (`token.children` with `dep_` in `{"advmod", "aux"}` — "may cause", "could lead to").
- Check for evidential framing ("studies show that X causes Y") -- the causal claim is attributed, not bare.
- Improve citation proximity check: current `has_nearby_citation()` uses a 100-char window; instead check if the citation is in the same sentence using sentence boundaries.

#### 3.4 — HedgeDetector: Clause-level dependency analysis

**File:** `src/academiclint/detectors/hedge.py`
**Problem:** Splits clauses on `,;:` characters (line 27), which is fragile. "Dr. Smith, who may have studied this, suggested..." splits incorrectly. Also, the hedge list includes "may" which matches inside words like "display" -- though word-boundary regex prevents this specific case, multi-word hedges like "tends to" and "appears to" can still be fragile.
**Fix:**
- Use spaCy's sentence and clause structure instead of splitting on punctuation.
- Identify hedges by their dependency role: auxiliary verbs ("may", "might", "could") modifying a main verb, adverbs ("possibly", "perhaps") modifying a verb.
- Count hedges per clause by traversing the dependency tree from the main verb.
- This gives accurate clause boundaries and avoids splitting on commas within relative clauses or appositives.

#### 3.5 — Density formula: Ground in data

**File:** `src/academiclint/density/calculator.py`
**Problem:** The formula `0.4 * content_ratio + 0.3 * unique_ratio + 0.3 * precision` and the grade thresholds (vapor < 0.2, crystalline >= 0.8) are arbitrary.
**Fix:**
- Collect a calibration set: 20 paragraphs of "good" academic writing (published journal abstracts) and 20 paragraphs of "bad" writing (undergraduate first drafts, AI-generated filler).
- Run both through the density calculator.
- Adjust weights and thresholds so that "good" writing consistently scores above 0.5 and "bad" writing consistently scores below 0.4.
- Document the calibration set and methodology in a `tests/calibration/` directory.
- Add a regression test that ensures calibration samples maintain their expected grade ranges.

#### 3.6 — Pipeline: Expose spaCy doc to detectors

**File:** `src/academiclint/core/pipeline.py`, `src/academiclint/detectors/base.py`
**Prerequisite for 3.1-3.4.**
**Current state:** `ProcessedDocument` stores `_spacy_doc` (line 74) but it's never accessed by detectors. Detectors receive `ProcessedDocument` and work only with the extracted token/sentence lists.
**Fix:**
- Add a public accessor method on `ProcessedDocument` that returns the spaCy doc: `@property def spacy_doc(self)`.
- Add helper methods to the `Detector` base class for common dependency queries:
  - `get_token_at(doc, char_offset)` — find the spaCy token at a character position.
  - `has_dependent(token, dep_labels)` — check if a token has children with specific dependency labels.
  - `get_clause_root(token)` — walk up the dependency tree to find the clause's root verb.
- These helpers keep the spaCy-specific logic in the base class, so individual detectors stay clean.

---

### PHASE 4: VALIDATE

| # | Action | Detail |
|---|--------|--------|
| 4.1 | Curate test corpus | Collect 10 real academic paper abstracts (diverse disciplines). Store in `tests/fixtures/real_papers/`. |
| 4.2 | Baseline measurement | Run current detectors against corpus. Record flag counts and manually classify each flag as true positive or false positive. |
| 4.3 | Post-improvement measurement | After Phase 3 changes, re-run against same corpus. Target: >50% reduction in false positives, <10% reduction in true positives. |
| 4.4 | Density calibration | Run density calculator against "good" and "bad" sample sets. Adjust formula weights until separation is clean. |
| 4.5 | Update tests | Replace `tests/test_env.py` (deleted) with new tests for dependency-aware detection. Add parametrized tests with real sentences for each detector improvement. |

---

### EXECUTION ORDER

```
Phase 1 (CUT)        →  1 day   →  Clean, passing tests, smaller codebase
Phase 3.6 (Pipeline)  →  1 day   →  spaCy doc accessible to detectors
Phase 3.1 (Vagueness) →  2 days  →  Highest-noise detector fixed first
Phase 3.2 (Circular)  →  1 day   →  Simplest improvement (swap stemmer for lemmatizer)
Phase 3.3 (Causal)    →  2 days  →  Dependency-aware causal claim analysis
Phase 3.4 (Hedge)     →  1 day   →  Dependency-aware clause identification
Phase 2 (DEFER)       →  1 day   →  Clean separation of optional components
Phase 3.5 (Density)   →  2 days  →  Requires test corpus (Phase 4.1)
Phase 4 (VALIDATE)    →  2 days  →  End-to-end validation against real papers
```

**Total estimated effort: ~13 working days**

---

### SUCCESS CRITERIA

After executing this plan, AcademicLint should:

1. **Be smaller.** ~2,500 fewer lines of code (1,546 cut + parts of deferred).
2. **Be smarter.** Detectors use spaCy's dependency parsing, not just regex word lists.
3. **Be quieter.** False positive rate on real academic text drops by >50%.
4. **Be honest.** No phantom domains, no fake streaming, no unused dependencies.
5. **Be grounded.** Density scores validated against a calibration corpus with documented methodology.
