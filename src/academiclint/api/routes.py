"""API routes for AcademicLint."""

try:
    from fastapi import APIRouter, HTTPException, status

    from academiclint import Config, Linter, __version__
    from academiclint.api.schemas import (
        CheckRequest,
        CheckResponse,
        DomainInfo,
        DomainsResponse,
        ErrorResponse,
        HealthResponse,
    )
    from academiclint.domains import DomainManager

    router = APIRouter()

    @router.post(
        "/check",
        response_model=CheckResponse,
        tags=["analysis"],
        summary="Analyze text for clarity issues",
        description="""
Analyze academic text for semantic clarity issues.

This endpoint performs comprehensive analysis including:
- **Semantic density calculation**: Measures meaningful content ratio
- **Issue detection**: Identifies 8 types of clarity problems
- **Actionable suggestions**: Provides specific improvements

### Strictness Levels
- `relaxed`: Minimal flagging, catches only severe issues
- `standard`: Balanced analysis for general academic writing
- `strict`: Thorough analysis for publication-ready work
- `academic`: Maximum strictness for peer-reviewed submissions

### Domains
Specify a domain to customize detection for your field:
`philosophy`, `computer-science`, `medicine`, `law`, `history`,
`psychology`, `economics`, `physics`, `biology`, `sociology`
        """,
        responses={
            200: {
                "description": "Analysis completed successfully",
                "model": CheckResponse,
            },
            400: {
                "description": "Invalid request (empty text or invalid config)",
                "model": ErrorResponse,
            },
            500: {
                "description": "Internal server error during analysis",
                "model": ErrorResponse,
            },
        },
    )
    async def check_text(request: CheckRequest):
        """Analyze text for semantic clarity issues."""
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty",
            )

        try:
            # Build config from request
            config = Config()
            if request.config:
                if request.config.level:
                    if request.config.level not in ("relaxed", "standard", "strict", "academic"):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid level '{request.config.level}'. Must be one of: relaxed, standard, strict, academic",
                        )
                    config.level = request.config.level
                if request.config.min_density is not None:
                    if not 0.0 <= request.config.min_density <= 1.0:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="min_density must be between 0.0 and 1.0",
                        )
                    config.min_density = request.config.min_density
                if request.config.domain:
                    config.domain = request.config.domain
                if request.config.domain_terms:
                    config.domain_terms = request.config.domain_terms

            linter = Linter(config)
            result = linter.check(request.text)

            # Convert to response format
            return _result_to_response(result)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    @router.get(
        "/health",
        response_model=HealthResponse,
        tags=["health"],
        summary="Health check",
        description="""
Check the health status of the API server.

Returns the current status, version, and whether NLP models are loaded.
Use this endpoint for:
- Load balancer health checks
- Kubernetes liveness/readiness probes
- Monitoring and alerting systems
        """,
        responses={
            200: {
                "description": "Service is healthy",
                "model": HealthResponse,
            },
        },
    )
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version=__version__,
            models_loaded=True,
        )

    @router.get(
        "/domains",
        response_model=DomainsResponse,
        tags=["domains"],
        summary="List available domains",
        description="""
List all available academic domain vocabularies.

Domains contain field-specific terminology that won't be flagged as jargon
when the domain is specified in analysis requests.

### Built-in Domains
- **philosophy**: Epistemology, ontology, ethics terminology
- **computer-science**: Programming, algorithms, systems terms
- **medicine**: Clinical, anatomical, pharmacological vocabulary
- **law**: Legal terminology and Latin phrases
- **history**: Historiographical and period-specific terms
- **psychology**: Cognitive, behavioral, clinical terms
- **economics**: Micro/macro economics vocabulary
- **physics**: Theoretical and applied physics terms
- **biology**: Molecular, ecological, evolutionary terms
- **sociology**: Social theory and research methodology terms
        """,
        responses={
            200: {
                "description": "List of available domains",
                "model": DomainsResponse,
            },
        },
    )
    async def list_domains():
        """List available domains."""
        manager = DomainManager()
        domains = manager.list_domains()
        return DomainsResponse(
            domains=[DomainInfo(**d) if isinstance(d, dict) else d for d in domains]
        )

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
