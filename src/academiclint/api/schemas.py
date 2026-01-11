"""Pydantic schemas for AcademicLint API."""

try:
    from typing import Optional

    from pydantic import BaseModel, Field


    class ConfigSchema(BaseModel):
        """Configuration options for analysis."""

        level: Optional[str] = Field(
            default="standard",
            description="Strictness level: relaxed, standard, strict, academic",
        )
        min_density: Optional[float] = Field(
            default=0.5,
            description="Minimum acceptable density (0.0-1.0)",
        )
        domain: Optional[str] = Field(
            default=None,
            description="Built-in domain name",
        )
        domain_terms: Optional[list[str]] = Field(
            default=None,
            description="Additional domain terms",
        )


    class CheckRequest(BaseModel):
        """Request body for /check endpoint."""

        text: str = Field(..., description="The text to analyze")
        config: Optional[ConfigSchema] = Field(
            default=None,
            description="Analysis configuration",
        )


    class SpanSchema(BaseModel):
        """Character span in text."""

        start: int
        end: int


    class FlagSchema(BaseModel):
        """A detected issue."""

        type: str
        term: str
        span: SpanSchema
        line: int
        column: int
        severity: str
        message: str
        suggestion: str
        example_revision: Optional[str] = None
        context: str


    class ParagraphSchema(BaseModel):
        """Analysis result for a paragraph."""

        index: int
        text: str
        span: SpanSchema
        density: float
        word_count: int
        sentence_count: int
        flags: list[FlagSchema]


    class SummarySchema(BaseModel):
        """Aggregate statistics."""

        density: float
        density_grade: str
        flag_count: int
        word_count: int
        sentence_count: int
        paragraph_count: int
        concept_count: int
        filler_ratio: float
        suggestion_count: int


    class CheckResponse(BaseModel):
        """Response body for /check endpoint."""

        id: str
        created_at: str
        input_length: int
        processing_time_ms: int
        summary: SummarySchema
        paragraphs: list[ParagraphSchema]
        overall_suggestions: list[str]


    class HealthResponse(BaseModel):
        """Response body for /health endpoint."""

        status: str
        version: str
        models_loaded: bool

except ImportError:
    # Pydantic not installed
    pass
