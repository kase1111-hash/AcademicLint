"""API routes for AcademicLint."""

try:
    from fastapi import APIRouter, HTTPException

    from academiclint import Config, Linter, __version__
    from academiclint.api.schemas import CheckRequest, CheckResponse, HealthResponse
    from academiclint.domains import DomainManager

    router = APIRouter()

    @router.post(
        "/check",
        response_model=CheckResponse,
        tags=["Analysis"],
        summary="Analyze text for clarity issues",
        response_description="Analysis results with density score and detected issues",
    )
    async def check_text(request: CheckRequest):
        """Analyze text for semantic clarity issues.

        Performs a comprehensive analysis of the provided text, detecting:
        - Vague or imprecise language
        - Excessive hedging
        - Circular definitions
        - Claims needing citations
        - Filler phrases and padding
        - Unsupported causal claims
        - Domain-specific jargon
        - Weasel words

        Returns a detailed report including per-paragraph density scores,
        individual flags for each detected issue, and improvement suggestions.
        """
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

    @router.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Check service health",
        response_description="Health status including version and model state",
    )
    async def health_check():
        """Health check endpoint.

        Returns the current health status of the API service,
        including version information and whether NLP models are loaded.
        Use this endpoint for monitoring and load balancer health checks.
        """
        return HealthResponse(
            status="healthy",
            version=__version__,
            models_loaded=True,
        )

    @router.get(
        "/domains",
        tags=["Configuration"],
        summary="List available domains",
        response_description="List of built-in domain configurations",
    )
    async def list_domains():
        """List available academic domains.

        Returns a list of built-in domain configurations that can be used
        to customize the analysis. Each domain includes specialized terminology
        that won't be flagged as jargon when analyzing domain-specific text.

        Available domains typically include: physics, biology, chemistry,
        medicine, computer_science, and more.
        """
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
