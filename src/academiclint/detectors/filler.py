"""Filler phrase detector for AcademicLint."""

import re

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType, Severity, Span
from academiclint.detectors.base import Detector
from academiclint.utils.patterns import FILLER_PHRASES


class FillerDetector(Detector):
    """Detector for filler phrases that add no information."""

    @property
    def flag_types(self) -> list[FlagType]:
        return [FlagType.FILLER]

    def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
        """Detect filler phrases in the document."""
        flags = []

        for phrase in FILLER_PHRASES:
            pattern = rf"\b{re.escape(phrase)}\b"

            for match in re.finditer(pattern, doc.text, re.IGNORECASE):
                start = match.start()
                end = match.end()

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
                    type=FlagType.FILLER,
                    term=term,
                    span=Span(start=start, end=end),
                    line=line,
                    column=column,
                    severity=Severity.LOW,
                    message="This phrase adds no specific information",
                    suggestion=self._get_suggestion(phrase),
                    context=context,
                )
                flags.append(flag)

        return flags

    def _get_suggestion(self, phrase: str) -> str:
        """Get suggestion for removing/replacing the filler."""
        suggestions = {
            "in today's society": "Remove or specify which society and time period",
            "in today's world": "Remove or be specific about context",
            "throughout history": "Specify the time period and region",
            "since the dawn of time": "Remove - adds no information",
            "it is important to note that": "Remove - just state the point",
            "it is worth noting that": "Remove - just state the point",
            "it goes without saying": "Remove - if it goes without saying, don't say it",
            "needless to say": "Remove - if needless, don't say it",
            "it is clear that": "Remove - if clear, just state the claim",
            "it is obvious that": "Remove - state the claim directly",
            "as we all know": "Remove or cite a source",
            "at the end of the day": "Remove - use specific conclusion",
            "when all is said and done": "Remove - be direct",
            "in terms of": "Remove or rephrase more directly",
            "the fact that": "Remove - just state the fact",
            "in order to": "Replace with 'to'",
        }
        return suggestions.get(phrase.lower(), "Remove or replace with specific content")
