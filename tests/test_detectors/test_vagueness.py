"""Tests for vagueness detector."""

import pytest

from academiclint.core.config import Config
from academiclint.core.pipeline import NLPPipeline
from academiclint.core.result import FlagType
from academiclint.detectors.vagueness import VaguenessDetector


class TestVaguenessDetector:
    """Tests for VaguenessDetector."""

    @pytest.fixture
    def detector(self):
        """Create a vagueness detector."""
        return VaguenessDetector()

    @pytest.fixture
    def config(self):
        """Create default config."""
        return Config()

    def test_detects_vague_terms(self, detector, config):
        """Test detection of vague terms."""
        # Create a simple mock ProcessedDocument
        from dataclasses import dataclass

        @dataclass
        class MockDoc:
            text: str
            sentences: list = None
            paragraphs: list = None

        doc = MockDoc(text="In society, things have changed significantly.")
        flags = detector.detect(doc, config)

        terms = [f.term.lower() for f in flags]
        assert "society" in terms or "things" in terms or "significantly" in terms

    def test_flag_types(self, detector):
        """Test that detector returns correct flag types."""
        assert FlagType.UNDERSPECIFIED in detector.flag_types

    def test_domain_terms_not_flagged(self, detector):
        """Test that domain terms are not flagged."""
        from dataclasses import dataclass

        @dataclass
        class MockDoc:
            text: str
            sentences: list = None
            paragraphs: list = None

        config = Config(domain_terms=["society"])
        doc = MockDoc(text="In society, we see patterns.")

        flags = detector.detect(doc, config)
        terms = [f.term.lower() for f in flags]

        # Society should not be flagged as it's a domain term
        assert "society" not in terms
