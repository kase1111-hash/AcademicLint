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

        # Build set of acceptable domain terms. Terms are compared by their word
        # tokens, as the text is: a single-token term ("C++") exempts that word,
        # and a multi-token term ("machine learning", "cross-validation") is
        # matched as a phrase whose words are not counted as jargon.
        domain_terms = {t.lower() for t in config.domain_terms}
        phrase_patterns = []
        for term in config.domain_terms:
            tokens = re.findall(r"\w+", term.lower())
            if len(tokens) == 1:
                domain_terms.add(tokens[0])
            elif len(tokens) > 1:
                phrase = r"\W+".join(map(re.escape, tokens))
                phrase_patterns.append(re.compile(rf"\b{phrase}\b", re.IGNORECASE))

        for sentence in doc.sentences:
            jargon_terms = []
            covered = [m.span() for p in phrase_patterns for m in p.finditer(sentence.text)]
            word_matches = list(re.finditer(r"\b\w+\b", sentence.text))
            words = [m.group() for m in word_matches]

            for match in word_matches:
                if any(start <= match.start() < end for start, end in covered):
                    continue
                if self._is_jargon(match.group(), domain_terms):
                    jargon_terms.append(match.group())

            if len(words) > 0:
                jargon_ratio = len(jargon_terms) / len(words)

                # Flag dense jargon unless the terms are explained nearby
                if (
                    jargon_ratio > self.JARGON_THRESHOLD
                    and len(jargon_terms) >= 3
                    and not self._has_explanations(sentence.text, jargon_terms)
                ):
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
