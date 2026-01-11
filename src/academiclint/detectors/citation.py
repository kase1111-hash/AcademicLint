"""Citation needed detector for AcademicLint."""

import re

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType, Severity, Span
from academiclint.detectors.base import Detector
from academiclint.utils.patterns import CITATION_PATTERNS, NEEDS_CITATION_PATTERNS


class CitationDetector(Detector):
    """Detector for claims that need citations."""

    @property
    def flag_types(self) -> list[FlagType]:
        return [FlagType.CITATION_NEEDED]

    def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
        """Detect claims that need citations."""
        flags = []

        for sentence in doc.sentences:
            for pattern in NEEDS_CITATION_PATTERNS:
                match = re.search(pattern, sentence.text, re.IGNORECASE)
                if match:
                    # Check if sentence has a citation
                    if self._has_citation(sentence.text):
                        continue

                    start = sentence.span.start
                    end = sentence.span.end

                    line = doc.text[:start].count("\n") + 1
                    line_start = doc.text.rfind("\n", 0, start) + 1
                    column = start - line_start + 1

                    matched_text = match.group(0)

                    flag = Flag(
                        type=FlagType.CITATION_NEEDED,
                        term=matched_text,
                        span=Span(start=start, end=end),
                        line=line,
                        column=column,
                        severity=self._get_severity(pattern),
                        message=self._get_message(matched_text),
                        suggestion="Add a citation to support this claim",
                        context=sentence.text,
                    )
                    flags.append(flag)
                    break  # One flag per sentence

        return flags

    def _has_citation(self, text: str) -> bool:
        """Check if text contains a citation."""
        for pattern in CITATION_PATTERNS:
            if re.search(pattern, text):
                return True
        return False

    def _get_severity(self, pattern: str) -> Severity:
        """Determine severity based on claim type."""
        # Statistics require citations
        if r"\d+%" in pattern:
            return Severity.HIGH
        # Superlatives need support
        if "first|largest|most|least" in pattern:
            return Severity.MEDIUM
        return Severity.MEDIUM

    def _get_message(self, matched_text: str) -> str:
        """Get explanation message for the claim."""
        if "%" in matched_text:
            return "Specific statistic requires a source"
        elif re.search(r"\d{4}", matched_text):
            return "Historical claim needs citation"
        elif "studies" in matched_text.lower() or "research" in matched_text.lower():
            return "'Studies show' without citation is a weasel pattern"
        elif "according to" in matched_text.lower():
            return "Attribution without specific source"
        return "This claim needs supporting evidence"
