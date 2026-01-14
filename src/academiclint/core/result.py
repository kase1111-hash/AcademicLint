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

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {"start": self.start, "end": self.end}


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

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "term": self.term,
            "span": self.span.to_dict(),
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "message": self.message,
            "suggestion": self.suggestion,
            "example_revision": self.example_revision,
            "context": self.context,
        }


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

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "index": self.index,
            "text": self.text,
            "span": self.span.to_dict(),
            "density": self.density,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "flags": [f.to_dict() for f in self.flags],
        }


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

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "density": self.density,
            "density_grade": self.density_grade,
            "flag_count": self.flag_count,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "paragraph_count": self.paragraph_count,
            "concept_count": self.concept_count,
            "filler_ratio": self.filler_ratio,
            "suggestion_count": self.suggestion_count,
        }


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

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "created_at": self.created_at,
            "input_length": self.input_length,
            "processing_time_ms": self.processing_time_ms,
            "summary": self.summary.to_dict(),
            "paragraphs": [p.to_dict() for p in self.paragraphs],
            "overall_suggestions": self.overall_suggestions,
        }
