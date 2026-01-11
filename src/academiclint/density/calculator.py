"""Semantic density calculation for AcademicLint."""

import re

from academiclint.core.config import Config
from academiclint.core.result import Flag, FlagType, Severity
from academiclint.utils.patterns import FUNCTION_WORDS


def calculate_density(text: str, flags: list[Flag], config: Config) -> float:
    """Calculate semantic density score for text.

    Components:
    1. Content word ratio (0.4 weight)
    2. Unique concept ratio (0.3 weight)
    3. Precision penalty (0.3 weight)

    Args:
        text: The text to analyze
        flags: List of flags for this text
        config: Linter configuration

    Returns:
        Float between 0.0 and 1.0
    """
    tokens = tokenize(text)
    if len(tokens) == 0:
        return 0.0

    # 1. Content word ratio
    content_words = [t for t in tokens if t.lower() not in FUNCTION_WORDS]
    content_ratio = len(content_words) / len(tokens) if tokens else 0

    # 2. Unique concept ratio (penalize repetition)
    lemmas = [lemmatize(t) for t in content_words]
    unique_ratio = len(set(lemmas)) / len(lemmas) if lemmas else 0

    # 3. Precision penalty (based on flags)
    flag_penalty = calculate_flag_penalty(flags, len(tokens))
    precision = 1.0 - flag_penalty

    # Weighted combination
    density = 0.4 * content_ratio + 0.3 * unique_ratio + 0.3 * precision

    return min(1.0, max(0.0, density))


def tokenize(text: str) -> list[str]:
    """Simple tokenization of text."""
    return re.findall(r"\b\w+\b", text)


def lemmatize(word: str) -> str:
    """Simple lemmatization - just lowercase and remove common suffixes."""
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
