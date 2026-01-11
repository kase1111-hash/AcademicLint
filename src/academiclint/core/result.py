"""Result data structures for AcademicLint analysis."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FlagType(Enum):
    """Types of issues that can be flagged."""

    UNDERSPECIFIED = "UNDERSPECIFIED"
    UNSUPPORTED_CAUSAL = "UNSUPPORTED_CAUSAL"
    CIRCULAR = "CIRCULAR"
    WEASEL = "WEASEL"
    HEDGE_STACK = "HEDGE_STACK"
    JARGON_DENSE = "JARGON_DENSE"
    CITATION_NEEDED = "CITATION_NEEDED"
    FILLER = "FILLER"


class Severity(Enum):
    """Severity levels for flagged issues."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Span:
    """Character-level position in source text."""

    start: int
    end: int


@dataclass
class Flag:
    """A single issue detected in the text."""

    type: FlagType
    term: str  # The flagged text
    span: Span  # Position in source
    line: int  # 1-indexed line number
    column: int  # 1-indexed column
    severity: Severity
    message: str  # Human-readable explanation
    suggestion: str  # How to fix it
    example_revision: Optional[str] = None  # Concrete rewrite example
    context: str = ""  # Surrounding text for display


@dataclass
class ParagraphResult:
    """Analysis result for a single paragraph."""

    index: int  # 0-indexed paragraph number
    text: str  # Original paragraph text
    span: Span  # Position in source
    density: float  # 0.0 - 1.0
    flags: list[Flag] = field(default_factory=list)
    word_count: int = 0
    sentence_count: int = 0


@dataclass
class Summary:
    """Aggregate statistics for entire document."""

    density: float  # Overall semantic density
    density_grade: str  # "vapor", "thin", "adequate", "dense", "crystalline"
    flag_count: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    concept_count: int  # Unique meaningful concepts
    filler_ratio: float  # Proportion of filler words
    suggestion_count: int


@dataclass
class AnalysisResult:
    """Complete analysis result for a document."""

    id: str  # Unique check ID (e.g., "check_abc123")
    created_at: str  # ISO 8601 timestamp
    input_length: int  # Character count of input
    processing_time_ms: int

    summary: Summary
    paragraphs: list[ParagraphResult] = field(default_factory=list)
    overall_suggestions: list[str] = field(default_factory=list)

    @property
    def density(self) -> float:
        """Convenience property for overall density."""
        return self.summary.density

    @property
    def flags(self) -> list[Flag]:
        """All flags across all paragraphs."""
        return [f for p in self.paragraphs for f in p.flags]
