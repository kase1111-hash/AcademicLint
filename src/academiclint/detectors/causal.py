"""Causal claim detector for AcademicLint."""

import re

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType, Severity
from academiclint.detectors.base import Detector
from academiclint.utils.patterns import CAUSAL_PATTERNS


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

                # Check if there's a citation nearby (uses base class method)
                if self.has_nearby_citation(doc.text, end):
                    continue

                term = doc.text[start:end]

                # Use base class create_flag helper for DRY
                flag = self.create_flag(
                    text=doc.text,
                    flag_type=FlagType.UNSUPPORTED_CAUSAL,
                    term=term,
                    start=start,
                    end=end,
                    severity=Severity.MEDIUM,
                    message="Causal claim without cited evidence or mechanism",
                    suggestion="Specify the mechanism, cite evidence, or use 'correlates with'",
                    example_revision=self._get_example(term),
                )
                flags.append(flag)

        return flags

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
