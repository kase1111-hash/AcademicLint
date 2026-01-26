"""Base detector interface for AcademicLint."""

import re
from abc import ABC, abstractmethod

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType, Span
from academiclint.utils.patterns import CITATION_PATTERNS


class Detector(ABC):
    """Base class for all detectors."""

    @abstractmethod
    def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
        """Detect issues in the processed document.

        Args:
            doc: NLP-processed document
            config: Linter configuration

        Returns:
            List of detected flags
        """
        pass

    @property
    @abstractmethod
    def flag_types(self) -> list[FlagType]:
        """Flag types this detector can produce."""
        pass

    # =========================================================================
    # Shared helper methods for all detectors (DRY principle)
    # =========================================================================

    def get_line_column(self, text: str, position: int) -> tuple[int, int]:
        """Get line and column number for a character position.

        Args:
            text: The full text
            position: Character position (0-indexed)

        Returns:
            Tuple of (line, column), both 1-indexed
        """
        line = text[:position].count("\n") + 1
        line_start = text.rfind("\n", 0, position) + 1
        column = position - line_start + 1
        return line, column

    # Common abbreviations that contain periods but don't end sentences
    _ABBREVIATIONS = frozenset({
        "dr.", "mr.", "mrs.", "ms.", "prof.", "sr.", "jr.",
        "etc.", "e.g.", "i.e.", "vs.", "viz.", "cf.",
        "fig.", "eq.", "no.", "vol.", "pp.", "ch.",
        "inc.", "ltd.", "corp.", "co.", "dept.",
        "jan.", "feb.", "mar.", "apr.", "jun.", "jul.",
        "aug.", "sep.", "sept.", "oct.", "nov.", "dec.",
    })

    def _is_sentence_boundary(self, text: str, period_pos: int) -> bool:
        """Check if a period at the given position is a sentence boundary.

        Args:
            text: The full text
            period_pos: Position of the period character

        Returns:
            True if this period ends a sentence, False otherwise
        """
        if period_pos < 0 or period_pos >= len(text):
            return False

        # Check for common abbreviations by looking backwards
        word_start = period_pos
        while word_start > 0 and text[word_start - 1].isalpha():
            word_start -= 1

        if word_start < period_pos:
            # Include the period in the potential abbreviation
            potential_abbrev = text[word_start:period_pos + 1].lower()
            if potential_abbrev in self._ABBREVIATIONS:
                return False

        # Check what follows the period (if anything)
        next_pos = period_pos + 1
        while next_pos < len(text) and text[next_pos] in " \t":
            next_pos += 1

        # If followed by newline or capital letter, likely a sentence boundary
        if next_pos >= len(text):
            return True
        if text[next_pos] == "\n":
            return True
        if text[next_pos].isupper():
            return True

        return False

    def get_sentence_context(self, text: str, start: int, end: int) -> str:
        """Extract the sentence containing a span.

        Args:
            text: The full text
            start: Start position of the span
            end: End position of the span

        Returns:
            The sentence containing the span
        """
        # Find sentence start by searching backwards for a true sentence boundary
        context_start = 0
        search_pos = start - 1
        while search_pos >= 0:
            if text[search_pos] == ".":
                if self._is_sentence_boundary(text, search_pos):
                    context_start = search_pos + 1
                    break
            elif text[search_pos] in "!?\n":
                context_start = search_pos + 1
                break
            search_pos -= 1

        # Find sentence end by searching forwards for a true sentence boundary
        context_end = len(text)
        search_pos = end
        while search_pos < len(text):
            if text[search_pos] == ".":
                if self._is_sentence_boundary(text, search_pos):
                    context_end = search_pos + 1
                    break
            elif text[search_pos] in "!?\n":
                context_end = search_pos + 1
                break
            search_pos += 1

        return text[context_start:context_end].strip()

    def get_window_context(self, text: str, start: int, end: int, window: int = 30) -> str:
        """Extract context window around a span.

        Args:
            text: The full text
            start: Start position of the span
            end: End position of the span
            window: Characters to include on each side

        Returns:
            Context string around the span
        """
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]

    def has_nearby_citation(
        self, text: str, position: int, window: int = 100, before: bool = False
    ) -> bool:
        """Check if there's a citation near the given position.

        Args:
            text: The full text
            position: Position to check from
            window: How far to search
            before: If True, search before position; if False, search after

        Returns:
            True if citation found nearby
        """
        if before:
            search_region = text[max(0, position - window) : position]
        else:
            search_region = text[position : position + window]

        for pattern in CITATION_PATTERNS:
            if re.search(pattern, search_region):
                return True
        return False

    def create_flag(
        self,
        text: str,
        flag_type: FlagType,
        term: str,
        start: int,
        end: int,
        severity,
        message: str,
        suggestion: str,
        example_revision: str = None,
        use_sentence_context: bool = True,
    ) -> Flag:
        """Create a Flag with common boilerplate handled.

        Args:
            text: The full document text
            flag_type: Type of flag
            term: The flagged text
            start: Start position
            end: End position
            severity: Severity level
            message: Human-readable explanation
            suggestion: How to fix it
            example_revision: Optional concrete rewrite
            use_sentence_context: If True, use sentence as context; else use window

        Returns:
            Configured Flag instance
        """
        line, column = self.get_line_column(text, start)

        if use_sentence_context:
            context = self.get_sentence_context(text, start, end)
        else:
            context = self.get_window_context(text, start, end)

        return Flag(
            type=flag_type,
            term=term,
            span=Span(start=start, end=end),
            line=line,
            column=column,
            severity=severity,
            message=message,
            suggestion=suggestion,
            example_revision=example_revision,
            context=context,
        )
