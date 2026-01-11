"""Jargon density detector for AcademicLint."""

import re

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType, Severity, Span
from academiclint.detectors.base import Detector
from academiclint.utils.patterns import COMMON_WORDS


class JargonDetector(Detector):
    """Detector for jargon-dense passages."""

    JARGON_THRESHOLD = 0.3  # Flag if >30% jargon without explanation

    @property
    def flag_types(self) -> list[FlagType]:
        return [FlagType.JARGON_DENSE]

    def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
        """Detect jargon-dense passages in the document."""
        flags = []

        # Build set of acceptable domain terms
        domain_terms = set(t.lower() for t in config.domain_terms)

        for sentence in doc.sentences:
            jargon_terms = []
            words = re.findall(r"\b\w+\b", sentence.text)

            for word in words:
                if self._is_jargon(word, domain_terms):
                    jargon_terms.append(word)

            if len(words) > 0:
                jargon_ratio = len(jargon_terms) / len(words)

                if jargon_ratio > self.JARGON_THRESHOLD and len(jargon_terms) >= 3:
                    # Check if terms are explained nearby
                    if not self._has_explanations(sentence.text, jargon_terms):
                        start = sentence.span.start
                        end = sentence.span.end

                        line = doc.text[:start].count("\n") + 1
                        line_start = doc.text.rfind("\n", 0, start) + 1
                        column = start - line_start + 1

                        flag = Flag(
                            type=FlagType.JARGON_DENSE,
                            term=", ".join(jargon_terms[:5]),
                            span=Span(start=start, end=end),
                            line=line,
                            column=column,
                            severity=Severity.MEDIUM,
                            message=f"{len(jargon_terms)} technical terms, {self._count_explanations(sentence.text)} explanations",
                            suggestion="Define technical terms or specify intended audience",
                            context=sentence.text,
                        )
                        flags.append(flag)

        return flags

    def _is_jargon(self, word: str, domain_terms: set) -> bool:
        """Check if a word is jargon."""
        word_lower = word.lower()

        # Not jargon if it's a common word
        if word_lower in COMMON_WORDS:
            return False

        # Not jargon if it's a domain term
        if word_lower in domain_terms:
            return False

        # Not jargon if it's too short
        if len(word) < 5:
            return False

        # Likely jargon if it has complex morphology
        complex_suffixes = ["ology", "ization", "ological", "istic", "ential"]
        for suffix in complex_suffixes:
            if word_lower.endswith(suffix):
                return True

        # Not in common words and reasonably long
        return len(word) >= 8

    def _has_explanations(self, text: str, terms: list[str]) -> bool:
        """Check if jargon terms are explained in the text."""
        explanation_patterns = [
            r"\([^)]+\)",  # Parenthetical explanation
            r", which means",
            r", i\.e\.,",
            r", that is,",
            r"refers to",
            r"defined as",
        ]

        explanation_count = 0
        for pattern in explanation_patterns:
            explanation_count += len(re.findall(pattern, text, re.IGNORECASE))

        # Has explanations if at least half the terms seem explained
        return explanation_count >= len(terms) / 2

    def _count_explanations(self, text: str) -> int:
        """Count explanation patterns in text."""
        explanation_patterns = [
            r"\([^)]+\)",
            r", which means",
            r", i\.e\.,",
            r", that is,",
            r"refers to",
            r"defined as",
        ]

        count = 0
        for pattern in explanation_patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count
