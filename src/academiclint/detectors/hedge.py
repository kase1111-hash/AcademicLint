"""Hedge stacking detector for AcademicLint."""

import re

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType, Severity, Span
from academiclint.detectors.base import Detector
from academiclint.utils.patterns import HEDGES


class HedgeDetector(Detector):
    """Detector for excessive hedge stacking."""

    HEDGE_THRESHOLD = 3  # Flag if 3+ hedges in one clause

    @property
    def flag_types(self) -> list[FlagType]:
        return [FlagType.HEDGE_STACK]

    def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
        """Detect hedge stacking in the document."""
        flags = []

        for sentence in doc.sentences:
            # Split sentence into clauses (roughly)
            clauses = re.split(r"[,;:]", sentence.text)

            for clause in clauses:
                hedge_count = self._count_hedges(clause)

                if hedge_count >= self.HEDGE_THRESHOLD:
                    # Find the clause in the original text
                    clause_stripped = clause.strip()
                    start = doc.text.find(clause_stripped)
                    if start == -1:
                        start = sentence.span.start
                    end = start + len(clause_stripped)

                    line = doc.text[:start].count("\n") + 1
                    line_start = doc.text.rfind("\n", 0, start) + 1
                    column = start - line_start + 1

                    confidence = self._estimate_confidence(hedge_count)

                    flag = Flag(
                        type=FlagType.HEDGE_STACK,
                        term=f"{hedge_count} hedges",
                        span=Span(start=start, end=end),
                        line=line,
                        column=column,
                        severity=Severity.MEDIUM if hedge_count < 5 else Severity.HIGH,
                        message=f"{hedge_count} hedges in one clause reduces confidence to ~{confidence:.0%}",
                        suggestion="Make a clear claim or acknowledge uncertainty cleanly",
                        context=clause_stripped,
                    )
                    flags.append(flag)

        return flags

    def _count_hedges(self, clause: str) -> int:
        """Count hedge words in a clause."""
        clause_lower = clause.lower()
        count = 0

        for hedge in HEDGES:
            if hedge.lower() in clause_lower:
                count += 1

        return count

    def _estimate_confidence(self, hedge_count: int) -> float:
        """Estimate remaining confidence after hedging."""
        # Each hedge reduces confidence by ~10%
        return 0.9**hedge_count
