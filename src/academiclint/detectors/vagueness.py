"""Vagueness detector for AcademicLint."""

import re

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType, Severity, Span
from academiclint.detectors.base import Detector
from academiclint.utils.patterns import VAGUE_TERMS


class VaguenessDetector(Detector):
    """Detector for underspecified/vague terms."""

    @property
    def flag_types(self) -> list[FlagType]:
        return [FlagType.UNDERSPECIFIED]

    def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
        """Detect vague/underspecified terms in the document."""
        flags = []
        text_lower = doc.text.lower()

        # Check for vague terms
        for term in VAGUE_TERMS:
            # Skip if it's a domain term
            if term.lower() in [t.lower() for t in config.domain_terms]:
                continue

            # Find all occurrences
            pattern = rf"\b{re.escape(term)}\b"
            for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                start = match.start()
                end = match.end()

                # Get original case from text
                original_term = doc.text[start:end]

                # Determine line and column
                line = doc.text[:start].count("\n") + 1
                line_start = doc.text.rfind("\n", 0, start) + 1
                column = start - line_start + 1

                # Get context
                context_start = max(0, start - 30)
                context_end = min(len(doc.text), end + 30)
                context = doc.text[context_start:context_end]

                # Determine severity based on term type
                severity = self._get_severity(term)

                flag = Flag(
                    type=FlagType.UNDERSPECIFIED,
                    term=original_term,
                    span=Span(start=start, end=end),
                    line=line,
                    column=column,
                    severity=severity,
                    message=self._get_message(term),
                    suggestion=self._get_suggestion(term),
                    context=context,
                )
                flags.append(flag)

        return flags

    def _get_severity(self, term: str) -> Severity:
        """Determine severity based on the term."""
        high_severity = {"things", "stuff", "society", "impact", "significant"}
        low_severity = {"very", "really", "quite", "rather"}

        if term.lower() in high_severity:
            return Severity.HIGH
        elif term.lower() in low_severity:
            return Severity.LOW
        return Severity.MEDIUM

    def _get_message(self, term: str) -> str:
        """Get explanation message for the term."""
        messages = {
            "society": "Which society? Western? American? Global?",
            "things": "What things specifically?",
            "stuff": "What specifically?",
            "significant": "Significant by what measure?",
            "impact": "What kind of impact? Measured how?",
            "important": "Important to whom? Why?",
            "interesting": "Interesting in what way?",
            "recently": "When exactly?",
            "often": "How often? With what frequency?",
            "sometimes": "Under what conditions?",
            "many": "How many? What proportion?",
            "some": "Which ones specifically?",
            "most": "What percentage? Based on what data?",
        }
        return messages.get(term.lower(), f"'{term}' lacks clear referent or scope")

    def _get_suggestion(self, term: str) -> str:
        """Get improvement suggestion for the term."""
        suggestions = {
            "society": "Specify which society and demographic",
            "things": "Name the specific items or concepts",
            "stuff": "Be specific about what you're referring to",
            "significant": "Quantify the significance or define the measure",
            "impact": "Specify the type and magnitude of impact",
            "important": "Explain the importance with specific reasons",
            "interesting": "Explain what makes it notable",
            "recently": "Provide a specific time frame",
            "often": "Provide frequency or proportion",
            "sometimes": "Specify the conditions or frequency",
            "many": "Provide a number or percentage",
            "some": "Identify which ones specifically",
            "most": "Cite the data or provide a percentage",
        }
        return suggestions.get(term.lower(), f"Specify what '{term}' refers to")
