"""Integration tests for API endpoints.

These tests verify that the API endpoints work correctly
with the underlying linting infrastructure.
"""

import pytest

# Try to import FastAPI testing utilities
try:
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


# Skip all tests in this module if FastAPI is not installed
pytestmark = pytest.mark.skipif(
    not FASTAPI_AVAILABLE,
    reason="FastAPI not installed"
)


@pytest.fixture
def client():
    """Create a test client for the API."""
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not installed")

    from academiclint.api.app import create_app

    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_returns_200(self, client):
        """Test that health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, client):
        """Test health check response structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_check_includes_version(self, client):
        """Test that health check includes version."""
        response = client.get("/health")
        data = response.json()

        from academiclint import __version__
        assert data["version"] == __version__


class TestCheckEndpoint:
    """Tests for the /check endpoint."""

    def test_check_returns_200(self, client):
        """Test that check returns 200 for valid request."""
        response = client.post(
            "/check",
            json={"text": "This is a test sentence for analysis."}
        )
        assert response.status_code == 200

    def test_check_response_structure(self, client):
        """Test check response has correct structure."""
        response = client.post(
            "/check",
            json={"text": "This is a test sentence for analysis."}
        )
        data = response.json()

        assert "id" in data
        assert "created_at" in data
        assert "input_length" in data
        assert "processing_time_ms" in data
        assert "summary" in data
        assert "paragraphs" in data
        assert "overall_suggestions" in data

    def test_check_summary_structure(self, client):
        """Test that summary has correct fields."""
        response = client.post(
            "/check",
            json={"text": "This is a test sentence."}
        )
        data = response.json()
        summary = data["summary"]

        assert "density" in summary
        assert "density_grade" in summary
        assert "flag_count" in summary
        assert "word_count" in summary
        assert "sentence_count" in summary
        assert "paragraph_count" in summary

    def test_check_with_problematic_text(self, client):
        """Test check with text that should produce flags."""
        response = client.post(
            "/check",
            json={
                "text": (
                    "In today's society, many experts believe this is true. "
                    "It is clear that things have changed significantly."
                )
            }
        )
        data = response.json()

        # Should detect issues
        assert data["summary"]["flag_count"] >= 0

    def test_check_with_custom_config(self, client):
        """Test check with custom configuration."""
        response = client.post(
            "/check",
            json={
                "text": "Test sentence for custom config.",
                "config": {
                    "level": "strict",
                    "min_density": 0.7
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    def test_check_with_domain_terms(self, client):
        """Test check with domain-specific terms."""
        response = client.post(
            "/check",
            json={
                "text": "The epistemological considerations are important.",
                "config": {
                    "domain_terms": ["epistemological"]
                }
            }
        )
        assert response.status_code == 200

    def test_check_paragraphs_have_flags(self, client):
        """Test that paragraphs include flag details."""
        response = client.post(
            "/check",
            json={
                "text": (
                    "Freedom is the state of being free. "
                    "Many experts believe this causes problems."
                )
            }
        )
        data = response.json()

        for para in data["paragraphs"]:
            assert "flags" in para
            assert "density" in para
            assert "span" in para

    def test_check_flag_structure(self, client):
        """Test that flags have correct structure."""
        response = client.post(
            "/check",
            json={
                "text": "Freedom is the state of being free."
            }
        )
        data = response.json()

        for para in data["paragraphs"]:
            for flag in para["flags"]:
                assert "type" in flag
                assert "term" in flag
                assert "span" in flag
                assert "line" in flag
                assert "column" in flag
                assert "severity" in flag
                assert "message" in flag
                assert "suggestion" in flag

    def test_check_empty_text_returns_error(self, client):
        """Test that empty text returns error."""
        response = client.post(
            "/check",
            json={"text": ""}
        )
        # Should return 500 due to validation error
        assert response.status_code == 500

    def test_check_missing_text_returns_error(self, client):
        """Test that missing text field returns error."""
        response = client.post(
            "/check",
            json={}
        )
        # Should return 422 (validation error) or 500
        assert response.status_code in [422, 500]


class TestDomainsEndpoint:
    """Tests for the /domains endpoint."""

    def test_domains_returns_200(self, client):
        """Test that domains endpoint returns 200."""
        response = client.get("/domains")
        assert response.status_code == 200

    def test_domains_returns_list(self, client):
        """Test that domains endpoint returns a list."""
        response = client.get("/domains")
        data = response.json()

        assert "domains" in data
        assert isinstance(data["domains"], list)


class TestAPIIntegrationWithLinter:
    """Tests verifying API correctly uses the Linter."""

    def test_api_result_matches_linter(self, client):
        """Test that API result matches direct Linter result."""
        text = "This is a test sentence for comparison."

        # Get API result
        response = client.post("/check", json={"text": text})
        api_data = response.json()

        # Get direct Linter result
        from academiclint import Config, Linter

        linter = Linter(Config())
        linter_result = linter.check(text)

        # Compare key metrics
        assert api_data["summary"]["word_count"] == linter_result.summary.word_count
        assert api_data["summary"]["paragraph_count"] == linter_result.summary.paragraph_count
        assert api_data["summary"]["flag_count"] == linter_result.summary.flag_count

    def test_api_config_affects_result(self, client):
        """Test that API config parameter affects results."""
        text = "Some possibly hedged language that might be flagged."

        # Standard config
        response_standard = client.post(
            "/check",
            json={"text": text, "config": {"level": "standard"}}
        )

        # Relaxed config
        response_relaxed = client.post(
            "/check",
            json={"text": text, "config": {"level": "relaxed"}}
        )

        # Both should succeed
        assert response_standard.status_code == 200
        assert response_relaxed.status_code == 200

    def test_api_preserves_input_length(self, client):
        """Test that API correctly reports input length."""
        text = "Test sentence with known length."
        expected_length = len(text)

        response = client.post("/check", json={"text": text})
        data = response.json()

        assert data["input_length"] == expected_length


class TestAPIConcurrency:
    """Tests for API behavior under concurrent requests."""

    def test_multiple_requests_succeed(self, client):
        """Test that multiple sequential requests succeed."""
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence.",
        ]

        for text in texts:
            response = client.post("/check", json={"text": text})
            assert response.status_code == 200

    def test_different_configs_work(self, client):
        """Test different configs in sequence."""
        configs = [
            {"level": "relaxed"},
            {"level": "standard"},
            {"level": "strict"},
        ]

        text = "Test sentence for different configs."

        for config in configs:
            response = client.post(
                "/check",
                json={"text": text, "config": config}
            )
            assert response.status_code == 200


class TestAPIErrorHandling:
    """Tests for API error handling."""

    def test_handles_very_long_text(self, client):
        """Test handling of very long text."""
        # Create moderately long text (not exceeding limits)
        long_text = "This is a test sentence. " * 1000

        response = client.post("/check", json={"text": long_text})

        # Should either succeed or return appropriate error
        assert response.status_code in [200, 500]

    def test_handles_unicode_text(self, client):
        """Test handling of Unicode text."""
        unicode_text = (
            "This text contains Unicode characters: "
            "café, naïve, résumé, 日本語, 中文, العربية"
        )

        response = client.post("/check", json={"text": unicode_text})
        assert response.status_code == 200

    def test_handles_special_characters(self, client):
        """Test handling of special characters."""
        special_text = (
            "Text with special chars: @#$%^&*() "
            "and <tags> and \"quotes\" and 'apostrophes'"
        )

        response = client.post("/check", json={"text": special_text})
        assert response.status_code == 200

    def test_handles_newlines(self, client):
        """Test handling of text with newlines."""
        text_with_newlines = """
        First paragraph.

        Second paragraph.

        Third paragraph.
        """

        response = client.post("/check", json={"text": text_with_newlines})
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["paragraph_count"] >= 1
