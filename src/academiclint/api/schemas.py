"""Pydantic schemas for AcademicLint API."""

try:
    from typing import Optional

    from pydantic import BaseModel, Field


    class ConfigSchema(BaseModel):
        """Configuration options for analysis."""

        level: Optional[str] = Field(
            default="standard",
            description="Strictness level: relaxed, standard, strict, academic",
            json_schema_extra={"example": "standard"},
        )
        min_density: Optional[float] = Field(
            default=0.5,
            ge=0.0,
            le=1.0,
            description="Minimum acceptable density (0.0-1.0)",
            json_schema_extra={"example": 0.5},
        )
        domain: Optional[str] = Field(
            default=None,
            description="Built-in domain name (e.g., philosophy, computer-science, medicine)",
            json_schema_extra={"example": "philosophy"},
        )
        domain_terms: Optional[list[str]] = Field(
            default=None,
            description="Additional domain-specific terms to exclude from jargon detection",
            json_schema_extra={"example": ["ontology", "epistemology", "hermeneutics"]},
        )

        model_config = {
            "json_schema_extra": {
                "examples": [
                    {"level": "standard", "domain": "philosophy"},
                    {"level": "strict", "min_density": 0.6, "domain_terms": ["phenomenology"]},
                ]
            }
        }


    class CheckRequest(BaseModel):
        """Request body for /check endpoint."""

        text: str = Field(
            ...,
            min_length=1,
            description="The academic text to analyze for semantic clarity issues",
            json_schema_extra={
                "example": "The phenomenon of consciousness is fundamentally important. Some researchers believe it emerges from neural processes."
            },
        )
        config: Optional[ConfigSchema] = Field(
            default=None,
            description="Optional analysis configuration. Uses defaults if not provided.",
        )

        model_config = {
            "json_schema_extra": {
                "examples": [
                    {
                        "text": "The ontological status of mathematical objects remains contentious. Platonists argue that numbers exist independently of human thought.",
                        "config": {"level": "standard", "domain": "philosophy"},
                    },
                    {
                        "text": "Research shows that the algorithm performs well in most cases.",
                        "config": {"level": "strict"},
                    },
                ]
            }
        }


    class SpanSchema(BaseModel):
        """Character span in text."""

        start: int = Field(..., ge=0, description="Start character position (0-indexed)")
        end: int = Field(..., ge=0, description="End character position (exclusive)")

        model_config = {"json_schema_extra": {"example": {"start": 15, "end": 27}}}


    class FlagSchema(BaseModel):
        """A detected semantic clarity issue."""

        type: str = Field(
            ...,
            description="Issue type: UNDERSPECIFIED, UNSUPPORTED_CAUSAL, CIRCULAR, WEASEL, HEDGE_STACK, JARGON_DENSE, CITATION_NEEDED, FILLER",
            json_schema_extra={"example": "WEASEL"},
        )
        term: str = Field(
            ...,
            description="The specific text that triggered the flag",
            json_schema_extra={"example": "Some researchers"},
        )
        span: SpanSchema = Field(..., description="Character positions of the flagged text")
        line: int = Field(..., ge=1, description="Line number (1-indexed)")
        column: int = Field(..., ge=1, description="Column number (1-indexed)")
        severity: str = Field(
            ...,
            description="Severity level: LOW, MEDIUM, HIGH",
            json_schema_extra={"example": "MEDIUM"},
        )
        message: str = Field(
            ...,
            description="Human-readable explanation of the issue",
            json_schema_extra={"example": "Vague attribution without specific source"},
        )
        suggestion: str = Field(
            ...,
            description="Actionable suggestion for improvement",
            json_schema_extra={"example": "Specify which researchers or cite sources"},
        )
        example_revision: Optional[str] = Field(
            default=None,
            description="Example of how to revise the text",
            json_schema_extra={"example": "Smith et al. (2023) argue that..."},
        )
        context: str = Field(
            ...,
            description="Surrounding text for context",
            json_schema_extra={"example": "...consciousness. Some researchers believe it emerges..."},
        )

        model_config = {
            "json_schema_extra": {
                "example": {
                    "type": "WEASEL",
                    "term": "Some researchers",
                    "span": {"start": 45, "end": 61},
                    "line": 2,
                    "column": 1,
                    "severity": "MEDIUM",
                    "message": "Vague attribution without specific source",
                    "suggestion": "Specify which researchers or cite sources",
                    "example_revision": "Smith et al. (2023) argue that...",
                    "context": "...consciousness. Some researchers believe it emerges...",
                }
            }
        }


    class ParagraphSchema(BaseModel):
        """Analysis result for a single paragraph."""

        index: int = Field(..., ge=0, description="Paragraph index (0-indexed)")
        text: str = Field(..., description="The paragraph text")
        span: SpanSchema = Field(..., description="Character span in original text")
        density: float = Field(
            ...,
            ge=0.0,
            le=1.0,
            description="Semantic density score (0.0-1.0, higher is better)",
        )
        word_count: int = Field(..., ge=0, description="Number of words in paragraph")
        sentence_count: int = Field(..., ge=0, description="Number of sentences in paragraph")
        flags: list[FlagSchema] = Field(
            ..., description="List of issues detected in this paragraph"
        )


    class SummarySchema(BaseModel):
        """Aggregate analysis statistics for the entire document."""

        density: float = Field(
            ...,
            ge=0.0,
            le=1.0,
            description="Overall semantic density score (0.0-1.0)",
            json_schema_extra={"example": 0.62},
        )
        density_grade: str = Field(
            ...,
            description="Qualitative grade: vapor (<0.3), thin (0.3-0.5), adequate (0.5-0.7), dense (0.7-0.85), crystalline (>0.85)",
            json_schema_extra={"example": "adequate"},
        )
        flag_count: int = Field(
            ..., ge=0, description="Total number of issues detected", json_schema_extra={"example": 5}
        )
        word_count: int = Field(
            ..., ge=0, description="Total word count", json_schema_extra={"example": 287}
        )
        sentence_count: int = Field(
            ..., ge=0, description="Total sentence count", json_schema_extra={"example": 12}
        )
        paragraph_count: int = Field(
            ..., ge=0, description="Total paragraph count", json_schema_extra={"example": 3}
        )
        concept_count: int = Field(
            ...,
            ge=0,
            description="Number of distinct concepts identified",
            json_schema_extra={"example": 15},
        )
        filler_ratio: float = Field(
            ...,
            ge=0.0,
            le=1.0,
            description="Ratio of filler words to total words",
            json_schema_extra={"example": 0.08},
        )
        suggestion_count: int = Field(
            ...,
            ge=0,
            description="Number of improvement suggestions",
            json_schema_extra={"example": 5},
        )

        model_config = {
            "json_schema_extra": {
                "example": {
                    "density": 0.62,
                    "density_grade": "adequate",
                    "flag_count": 5,
                    "word_count": 287,
                    "sentence_count": 12,
                    "paragraph_count": 3,
                    "concept_count": 15,
                    "filler_ratio": 0.08,
                    "suggestion_count": 5,
                }
            }
        }


    class CheckResponse(BaseModel):
        """Response body for /check endpoint containing full analysis results."""

        id: str = Field(
            ...,
            description="Unique identifier for this analysis",
            json_schema_extra={"example": "check_a1b2c3d4"},
        )
        created_at: str = Field(
            ...,
            description="ISO 8601 timestamp of analysis",
            json_schema_extra={"example": "2025-01-11T10:30:00Z"},
        )
        input_length: int = Field(
            ..., ge=0, description="Length of input text in characters", json_schema_extra={"example": 1547}
        )
        processing_time_ms: int = Field(
            ..., ge=0, description="Processing time in milliseconds", json_schema_extra={"example": 234}
        )
        summary: SummarySchema = Field(..., description="Aggregate statistics")
        paragraphs: list[ParagraphSchema] = Field(
            ..., description="Per-paragraph analysis results"
        )
        overall_suggestions: list[str] = Field(
            ...,
            description="Document-level improvement suggestions",
            json_schema_extra={"example": ["Consider adding citations to support causal claims"]},
        )


    class HealthResponse(BaseModel):
        """Response body for /health endpoint."""

        status: str = Field(
            ...,
            description="Service status: 'healthy' or 'unhealthy'",
            json_schema_extra={"example": "healthy"},
        )
        version: str = Field(
            ...,
            description="API version string",
            json_schema_extra={"example": "1.0.0"},
        )
        models_loaded: bool = Field(
            ...,
            description="Whether NLP models are loaded and ready",
            json_schema_extra={"example": True},
        )

        model_config = {
            "json_schema_extra": {
                "example": {"status": "healthy", "version": "1.0.0", "models_loaded": True}
            }
        }


    class DomainInfo(BaseModel):
        """Information about an available domain."""

        name: str = Field(
            ...,
            description="Domain identifier",
            json_schema_extra={"example": "philosophy"},
        )
        term_count: int = Field(
            ...,
            ge=0,
            description="Number of terms in domain vocabulary",
            json_schema_extra={"example": 150},
        )
        description: Optional[str] = Field(
            default=None,
            description="Human-readable description of the domain",
            json_schema_extra={"example": "Philosophy and critical theory terminology"},
        )


    class DomainsResponse(BaseModel):
        """Response body for /domains endpoint."""

        domains: list[DomainInfo] = Field(
            ..., description="List of available domains"
        )

        model_config = {
            "json_schema_extra": {
                "example": {
                    "domains": [
                        {"name": "philosophy", "term_count": 150, "description": "Philosophy terminology"},
                        {"name": "computer-science", "term_count": 200, "description": "CS and programming terms"},
                    ]
                }
            }
        }


    class ErrorResponse(BaseModel):
        """Standard error response format."""

        detail: str = Field(
            ...,
            description="Error message describing what went wrong",
            json_schema_extra={"example": "Text cannot be empty"},
        )

        model_config = {
            "json_schema_extra": {
                "examples": [
                    {"detail": "Text cannot be empty"},
                    {"detail": "Invalid level 'extreme'. Must be one of: relaxed, standard, strict, academic"},
                    {"detail": "min_density must be between 0.0 and 1.0"},
                ]
            }
        }


except ImportError:
    # Pydantic not installed
    pass
