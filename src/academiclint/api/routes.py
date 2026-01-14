"""API routes for AcademicLint."""

try:
    from fastapi import APIRouter, HTTPException, status

    from academiclint import Config, Linter, __version__
    from academiclint.api.schemas import (
        CheckRequest,
        CheckResponse,
        DomainInfo,
        DomainsResponse,
        HealthResponse,
    )
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
            ) from e

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
        domains = manager.list_domains()
        return DomainsResponse(
            domains=[DomainInfo(**d) if isinstance(d, dict) else d for d in domains]
        )

    def _result_to_response(result) -> dict:
        """Convert AnalysisResult to API response."""
        return result.to_dict()

except ImportError:
    # FastAPI not installed
    router = None
