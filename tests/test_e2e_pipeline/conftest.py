"""Pytest configuration for end-to-end pipeline tests.

Provides fixtures and marks for tests that require NLP models.
"""

import pytest


def is_spacy_model_available():
    """Check if required spaCy model is available."""
    try:
        import spacy
        spacy.load("en_core_web_lg")
        return True
    except (ImportError, OSError):
        try:
            import spacy
            spacy.load("en_core_web_sm")
            return True
        except (ImportError, OSError):
            return False


# Skip all tests in this package if model not available
requires_spacy = pytest.mark.skipif(
    not is_spacy_model_available(),
    reason="spaCy model not available. Run: python -m spacy download en_core_web_lg"
)


def pytest_collection_modifyitems(config, items):
    """Add markers to tests that require NLP models."""
    for item in items:
        # All tests in this package require the NLP model
        if "test_e2e_pipeline" in str(item.fspath):
            item.add_marker(requires_spacy)


@pytest.fixture
def spacy_model_check():
    """Fixture that ensures spaCy model is available."""
    if not is_spacy_model_available():
        pytest.skip("spaCy model not available")
