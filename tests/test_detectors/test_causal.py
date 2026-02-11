"""Tests for causal claim detector."""

import pytest

from academiclint.core.config import Config
from academiclint.core.result import FlagType
from academiclint.detectors.causal import CausalDetector


class TestCausalDetector:
    """Tests for CausalDetector."""

    @pytest.fixture
    def detector(self):
        """Create a causal detector."""
        return CausalDetector()

    @pytest.fixture
    def config(self):
        """Create default config."""
        return Config()

    def test_detects_causal_claims(self, detector, config):
        """Test detection of causal claims."""
        from dataclasses import dataclass

        @dataclass
        class MockDoc:
            text: str
            sentences: list = None
            paragraphs: list = None

            def get_sentence_for_span(self, start, end):
                if not self.sentences:
                    return None
                for sent in self.sentences:
                    if hasattr(sent, 'span') and sent.span.start <= start and end <= sent.span.end:
                        return sent
                return None

        doc = MockDoc(text="Social media causes depression in teenagers.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any("cause" in f.term.lower() for f in flags)

    def test_flag_types(self, detector):
        """Test that detector returns correct flag types."""
        assert FlagType.UNSUPPORTED_CAUSAL in detector.flag_types

    def test_cited_claims_not_flagged(self, detector, config):
        """Test that claims with citations are not flagged."""
        from dataclasses import dataclass

        @dataclass
        class MockDoc:
            text: str
            sentences: list = None
            paragraphs: list = None

            def get_sentence_for_span(self, start, end):
                if not self.sentences:
                    return None
                for sent in self.sentences:
                    if hasattr(sent, 'span') and sent.span.start <= start and end <= sent.span.end:
                        return sent
                return None

        doc = MockDoc(text="Social media causes depression (Smith, 2023).")
        flags = detector.detect(doc, config)

        # Should have fewer or no flags due to citation
        assert len(flags) == 0 or all("cause" not in f.term.lower() for f in flags)

    def test_detects_multiple_causal_patterns(self, detector, config):
        """Test detection of various causal patterns."""
        from dataclasses import dataclass

        @dataclass
        class MockDoc:
            text: str
            sentences: list = None
            paragraphs: list = None

            def get_sentence_for_span(self, start, end):
                if not self.sentences:
                    return None
                for sent in self.sentences:
                    if hasattr(sent, 'span') and sent.span.start <= start and end <= sent.span.end:
                        return sent
                return None

        doc = MockDoc(
            text="The policy led to changes. This resulted in improvements. Due to the weather."
        )
        flags = detector.detect(doc, config)

        # Should detect multiple causal patterns
        assert len(flags) >= 1
