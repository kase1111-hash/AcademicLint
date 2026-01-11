"""Causal claim detector for AcademicLint."""

import re

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType, Severity, Span
from academiclint.detectors.base import Detector
from academiclint.utils.patterns import CAUSAL_PATTERNS, CITATION_PATTERNS


class CausalDetector(Detector):
    """Detector for unsupported causal claims."""

    @property
    def flag_types(self) -> list[FlagType]:
        return [FlagType.UNSUPPORTED_CAUSAL]

    def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
        """Detect unsupported causal claims in the document."""
        flags = []

        for pattern in CAUSAL_PATTERNS:
            for match in re.finditer(pattern, doc.text, re.IGNORECASE):
                start = match.start()
                end = match.end()

                # Check if there's a citation nearby
                if self._has_nearby_citation(doc.text, end):
                    continue

                # Get the matched term
                term = doc.text[start:end]

                # Determine line and column
                line = doc.text[:start].count("\n") + 1
                line_start = doc.text.rfind("\n", 0, start) + 1
                column = start - line_start + 1

                # Get context (the sentence containing the causal claim)
                context_start = max(0, doc.text.rfind(".", 0, start) + 1)
                context_end = doc.text.find(".", end)
                if context_end == -1:
                    context_end = min(len(doc.text), end + 50)
                else:
                    context_end += 1
                context = doc.text[context_start:context_end].strip()

                flag = Flag(
                    type=FlagType.UNSUPPORTED_CAUSAL,
                    term=term,
                    span=Span(start=start, end=end),
                    line=line,
                    column=column,
                    severity=Severity.MEDIUM,
                    message="Causal claim without cited evidence or mechanism",
                    suggestion="Specify the mechanism, cite evidence, or use 'correlates with'",
                    example_revision=self._get_example(term),
                    context=context,
                )
                flags.append(flag)

        return flags

    def _has_nearby_citation(self, text: str, position: int, window: int = 100) -> bool:
        """Check if there's a citation near the given position."""
        search_region = text[position : position + window]

        for pattern in CITATION_PATTERNS:
            if re.search(pattern, search_region):
                return True
        return False

    def _get_example(self, term: str) -> str:
        """Get example revision for the causal term."""
        term_lower = term.lower().strip()

        if "cause" in term_lower:
            return "Consider: 'correlates with' or 'is associated with'"
        elif "lead" in term_lower:
            return "Consider: 'is followed by' or 'precedes'"
        elif "result" in term_lower:
            return "Consider: 'is associated with' or specify the mechanism"
        elif "due to" in term_lower:
            return "Consider: 'associated with' or cite evidence for causation"

        return "Consider using correlational language unless causation is established"
