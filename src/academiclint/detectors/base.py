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

    def get_sentence_context(self, text: str, start: int, end: int) -> str:
        """Extract the sentence containing a span.

        Args:
            text: The full text
            start: Start position of the span
            end: End position of the span

        Returns:
            The sentence containing the span
        """
        # Find sentence boundaries
        context_start = max(0, text.rfind(".", 0, start) + 1)
        context_end = text.find(".", end)
        if context_end == -1:
            context_end = min(len(text), end + 50)
        else:
            context_end += 1
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
