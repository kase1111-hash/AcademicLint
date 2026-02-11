"""Weasel word detector for AcademicLint."""

import re

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType, Severity
from academiclint.detectors.base import Detector
from academiclint.utils.patterns import WEASEL_PATTERNS


class WeaselDetector(Detector):
    """Detector for weasel words and phrases."""

    @property
    def flag_types(self) -> list[FlagType]:
        return [FlagType.WEASEL]

    def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
        """Detect weasel words in the document."""
        flags = []

        # Get all patterns including custom ones
        patterns = list(WEASEL_PATTERNS)
        for weasel in config.additional_weasels:
            patterns.append(rf"\b{re.escape(weasel)}\b")

        for pattern in patterns:
            for match in re.finditer(pattern, doc.text, re.IGNORECASE):
                start = match.start()
                end = match.end()

                # Check if there's a citation in the same sentence
                if self.has_citation_in_sentence(doc, start, end):
                    continue

                term = doc.text[start:end]

                # Use base class create_flag helper for DRY
                flag = self.create_flag(
                    text=doc.text,
                    flag_type=FlagType.WEASEL,
                    term=term,
                    start=start,
                    end=end,
                    severity=Severity.MEDIUM,
                    message="Vague attribution that avoids accountability",
                    suggestion=self._get_suggestion(term),
                )
                flags.append(flag)

        return flags

    def _get_suggestion(self, term: str) -> str:
        """Get suggestion for the weasel phrase."""
        term_lower = term.lower()

        if "some" in term_lower or "many" in term_lower or "most" in term_lower:
            return "Name specific sources or cite references"
        elif "it is" in term_lower or "it's" in term_lower:
            return "State who believes this and cite the source"
        elif "research" in term_lower or "studies" in term_lower:
            return "Cite the specific research or studies"
        elif "according to" in term_lower:
            return "Name the specific source"

        return "Provide specific attribution with citations"
