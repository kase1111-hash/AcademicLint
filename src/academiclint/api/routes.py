"""API routes for AcademicLint."""

try:
    from fastapi import APIRouter, HTTPException

    from academiclint import Config, Linter, __version__
    from academiclint.api.schemas import CheckRequest, CheckResponse, HealthResponse
    from academiclint.domains import DomainManager

    router = APIRouter()

    @router.post("/check", response_model=CheckResponse)
    async def check_text(request: CheckRequest):
        """Analyze text for semantic clarity issues."""
        try:
            # Build config from request
            config = Config()
            if request.config:
                if request.config.level:
                    config.level = request.config.level
                if request.config.min_density is not None:
                    config.min_density = request.config.min_density
                if request.config.domain:
                    config.domain = request.config.domain
                if request.config.domain_terms:
                    config.domain_terms = request.config.domain_terms

            linter = Linter(config)
            result = linter.check(request.text)

            # Convert to response format
            return _result_to_response(result)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version=__version__,
            models_loaded=True,
        )

    @router.get("/domains")
    async def list_domains():
        """List available domains."""
        manager = DomainManager()
        return {"domains": manager.list_domains()}

    def _result_to_response(result) -> dict:
        """Convert AnalysisResult to API response."""
        paragraphs = []
        for para in result.paragraphs:
            flags = []
            for flag in para.flags:
                flags.append({
                    "type": flag.type.value,
                    "term": flag.term,
                    "span": {"start": flag.span.start, "end": flag.span.end},
                    "line": flag.line,
                    "column": flag.column,
                    "severity": flag.severity.value,
                    "message": flag.message,
                    "suggestion": flag.suggestion,
                    "example_revision": flag.example_revision,
                    "context": flag.context,
                })

            paragraphs.append({
                "index": para.index,
                "text": para.text,
                "span": {"start": para.span.start, "end": para.span.end},
                "density": para.density,
                "word_count": para.word_count,
                "sentence_count": para.sentence_count,
                "flags": flags,
            })

        return {
            "id": result.id,
            "created_at": result.created_at,
            "input_length": result.input_length,
            "processing_time_ms": result.processing_time_ms,
            "summary": {
                "density": result.summary.density,
                "density_grade": result.summary.density_grade,
                "flag_count": result.summary.flag_count,
                "word_count": result.summary.word_count,
                "sentence_count": result.summary.sentence_count,
                "paragraph_count": result.summary.paragraph_count,
                "concept_count": result.summary.concept_count,
                "filler_ratio": result.summary.filler_ratio,
                "suggestion_count": result.summary.suggestion_count,
            },
            "paragraphs": paragraphs,
            "overall_suggestions": result.overall_suggestions,
        }

except ImportError:
    # FastAPI not installed
    router = None
