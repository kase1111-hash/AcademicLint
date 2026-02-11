"""Semantic density calculation for AcademicLint."""

import re
from typing import Optional

from academiclint.core.config import Config
from academiclint.core.result import Flag, FlagType, Severity
from academiclint.utils.patterns import FUNCTION_WORDS


def calculate_density(
    text: str,
    flags: list[Flag],
    config: Config,
    tokens_with_lemmas: Optional[list[tuple[str, str, bool]]] = None,
) -> float:
    """Calculate semantic density score for text.

    Components:
    1. Content word ratio (0.25 weight) — proportion of non-function words
    2. Unique concept ratio (0.25 weight) — penalizes repetitive vocabulary
    3. Specificity score (0.20 weight) — rewards numbers, proper nouns, technical terms
    4. Precision (0.30 weight) — penalizes detected issues (flags)

    The specificity component distinguishes precise academic writing (with
    data, citations, specific nouns) from vague writing that uses many
    content words but says little.

    Args:
        text: The text to analyze
        flags: List of flags for this text
        config: Linter configuration
        tokens_with_lemmas: Optional list of (text, lemma, is_stop) tuples
            from spaCy processing. If provided, uses spaCy's lemmatization
            instead of the simple suffix-stripping fallback.

    Returns:
        Float between 0.0 and 1.0
    """
    if tokens_with_lemmas is not None:
        # Use pre-computed tokens from spaCy (more accurate)
        if len(tokens_with_lemmas) == 0:
            return 0.0

        token_count = len(tokens_with_lemmas)

        # 1. Content word ratio (non-stop words)
        content_tokens = [
            (text, lemma) for text, lemma, is_stop in tokens_with_lemmas
            if not is_stop and text.lower() not in FUNCTION_WORDS
        ]
        content_ratio = len(content_tokens) / token_count if token_count else 0

        # 2. Unique concept ratio using spaCy lemmas
        lemmas = [lemma.lower() for _, lemma in content_tokens]
        unique_ratio = len(set(lemmas)) / len(lemmas) if lemmas else 0
    else:
        # Fallback to simple tokenization and lemmatization
        tokens = tokenize(text)
        if len(tokens) == 0:
            return 0.0

        token_count = len(tokens)

        # 1. Content word ratio
        content_words = [t for t in tokens if t.lower() not in FUNCTION_WORDS]
        content_ratio = len(content_words) / token_count if token_count else 0

        # 2. Unique concept ratio (penalize repetition)
        lemmas = [lemmatize(t) for t in content_words]
        unique_ratio = len(set(lemmas)) / len(lemmas) if lemmas else 0

    # 3. Specificity score — rewards concrete, precise language
    specificity = _calculate_specificity(text, token_count)

    # 4. Precision penalty (based on flags)
    flag_penalty = calculate_flag_penalty(flags, token_count)
    precision = 1.0 - flag_penalty

    # Weighted combination
    density = (
        0.25 * content_ratio
        + 0.25 * unique_ratio
        + 0.20 * specificity
        + 0.30 * precision
    )

    return min(1.0, max(0.0, density))


def _calculate_specificity(text: str, token_count: int) -> float:
    """Score how specific/concrete the text is.

    Rewards:
    - Numbers and percentages (quantitative claims)
    - Parenthetical citations
    - Capitalized multi-letter words mid-sentence (proper nouns, acronyms)
    - Technical patterns (hyphenated compounds, slash-separated terms)

    Returns:
        Float between 0.0 and 1.0
    """
    if token_count == 0:
        return 0.0

    markers = 0

    # Numbers: "42", "3.14", "1,003", "14.9%"
    markers += len(re.findall(r"\b\d[\d,.]*%?\b", text))

    # Parenthetical citations: (Author, 2020), (Author et al., 2020), [1]
    markers += len(re.findall(r"\([A-Z][a-z]+.*?\d{4}\)", text))
    markers += len(re.findall(r"\[\d+\]", text))

    # Capitalized words mid-sentence (proper nouns, acronyms like "LIGO", "DMN")
    # Exclude sentence-initial words
    markers += len(re.findall(r"(?<=[.!?]\s)[^A-Z]*?\b([A-Z]{2,})\b", text))
    markers += len(re.findall(r"\b[A-Z]{2,}\b", text))

    # Technical compounds: "CRISPR-Cas9", "DMN-FPCN", "difference-in-differences"
    markers += len(re.findall(r"\b\w+-\w+(?:-\w+)*\b", text))

    # Comparison operators and statistical notation: "p < 0.001", "r = 0.31"
    markers += len(re.findall(r"[<>=≤≥]\s*\d", text))

    # Normalize: ~1 marker per 10 tokens = good specificity (1.0)
    ratio = markers / (token_count / 10)
    return min(1.0, ratio)


def tokenize(text: str) -> list[str]:
    """Simple tokenization of text."""
    return re.findall(r"\b\w+\b", text)


def lemmatize(word: str) -> str:
    """Simple lemmatization fallback - lowercase and remove common suffixes.

    Note: This is a fallback for when spaCy tokens are not available.
    For better accuracy, pass tokens_with_lemmas to calculate_density().
    """
    word = word.lower()

    # Remove common suffixes
    suffixes = ["ing", "ed", "er", "est", "ly", "ness", "ment", "tion", "sion", "ity"]
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[: -len(suffix)]

    return word


def calculate_flag_penalty(flags: list[Flag], token_count: int) -> float:
    """Calculate penalty based on flag count and severity."""
    weights = {
        Severity.LOW: 0.02,
        Severity.MEDIUM: 0.05,
        Severity.HIGH: 0.10,
    }

    total_penalty = sum(weights.get(f.severity, 0.05) for f in flags)

    # Normalize per 50 tokens
    normalized = total_penalty / max(token_count / 50, 1)

    # Cap at 50% penalty
    return min(0.5, normalized)
