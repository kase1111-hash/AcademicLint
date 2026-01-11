"""Circular definition detector for AcademicLint."""

import re

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType, Severity, Span
from academiclint.detectors.base import Detector


class CircularDetector(Detector):
    """Detector for circular definitions."""

    # Patterns for definition structures
    DEFINITION_PATTERNS = [
        r"(\w+)\s+(?:is|are|means?|refers?\s+to)\s+(?:a|an|the)?\s*(.*)",
    ]

    @property
    def flag_types(self) -> list[FlagType]:
        return [FlagType.CIRCULAR]

    def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
        """Detect circular definitions in the document."""
        flags = []

        for sentence in doc.sentences:
            for pattern in self.DEFINITION_PATTERNS:
                match = re.match(pattern, sentence.text, re.IGNORECASE)
                if match:
                    term = match.group(1)
                    definition = match.group(2)

                    # Check for circularity
                    if self._is_circular(term, definition):
                        start = sentence.span.start
                        end = sentence.span.end

                        line = doc.text[:start].count("\n") + 1
                        line_start = doc.text.rfind("\n", 0, start) + 1
                        column = start - line_start + 1

                        flag = Flag(
                            type=FlagType.CIRCULAR,
                            term=term,
                            span=Span(start=start, end=end),
                            line=line,
                            column=column,
                            severity=Severity.HIGH,
                            message=f"'{term}' is defined using a form of itself",
                            suggestion="Define in terms of specific properties or examples",
                            example_revision=self._get_example(term),
                            context=sentence.text,
                        )
                        flags.append(flag)

        return flags

    def _is_circular(self, term: str, definition: str) -> bool:
        """Check if a definition is circular."""
        # Get the root/lemma of the term
        term_lower = term.lower()
        term_root = self._get_root(term_lower)

        # Tokenize definition
        words = re.findall(r"\b\w+\b", definition.lower())

        # Check if any word in definition shares root with term
        for word in words:
            word_root = self._get_root(word)
            if term_root == word_root or term_lower == word:
                return True

        return False

    def _get_root(self, word: str) -> str:
        """Get a simple root form of a word."""
        # Simple stemming - remove common suffixes
        suffixes = ["ness", "ment", "tion", "sion", "ing", "ed", "er", "est", "ly", "ity", "dom"]

        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[: -len(suffix)]

        return word

    def _get_example(self, term: str) -> str:
        """Get example of non-circular definition."""
        examples = {
            "freedom": "the ability to act without external constraint in domain X",
            "democracy": "a system where citizens vote to select representatives",
            "justice": "the fair distribution of benefits and burdens in society",
            "love": "a strong affection characterized by care and commitment",
        }
        return examples.get(
            term.lower(),
            f"Define '{term}' using properties, examples, or necessary/sufficient conditions",
        )
