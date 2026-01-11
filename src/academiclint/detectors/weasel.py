"""Weasel word detector for AcademicLint."""

import re

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType, Severity, Span
from academiclint.detectors.base import Detector
from academiclint.utils.patterns import CITATION_PATTERNS, WEASEL_PATTERNS


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

                # Check if followed by citation
                if self._has_following_citation(doc.text, end):
                    continue

                term = doc.text[start:end]

                line = doc.text[:start].count("\n") + 1
                line_start = doc.text.rfind("\n", 0, start) + 1
                column = start - line_start + 1

                # Get context
                context_start = max(0, doc.text.rfind(".", 0, start) + 1)
                context_end = doc.text.find(".", end)
                if context_end == -1:
                    context_end = min(len(doc.text), end + 50)
                else:
                    context_end += 1
                context = doc.text[context_start:context_end].strip()

                flag = Flag(
                    type=FlagType.WEASEL,
                    term=term,
                    span=Span(start=start, end=end),
                    line=line,
                    column=column,
                    severity=Severity.MEDIUM,
                    message="Vague attribution that avoids accountability",
                    suggestion=self._get_suggestion(term),
                    context=context,
                )
                flags.append(flag)

        return flags

    def _has_following_citation(self, text: str, position: int, window: int = 20) -> bool:
        """Check if there's a citation immediately following."""
        search_region = text[position : position + window]

        for pattern in CITATION_PATTERNS:
            if re.match(r"\s*" + pattern, search_region):
                return True
        return False

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
