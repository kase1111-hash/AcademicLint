"""Tests for weasel word detector."""

from dataclasses import dataclass

import pytest

from academiclint.core.config import Config
from academiclint.core.result import FlagType
from academiclint.detectors.weasel import WeaselDetector


@dataclass
class MockDoc:
    """Mock ProcessedDocument for testing."""

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


class TestWeaselDetector:
    """Tests for WeaselDetector."""

    @pytest.fixture
    def detector(self):
        """Create a weasel detector."""
        return WeaselDetector()

    @pytest.fixture
    def config(self):
        """Create default config."""
        return Config()

    def test_flag_types(self, detector):
        """Test that detector returns correct flag types."""
        assert FlagType.WEASEL in detector.flag_types

    def test_detects_many_experts(self, detector, config):
        """Test detection of 'many experts' pattern."""
        doc = MockDoc(text="Many experts believe this is true.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        terms = [f.term.lower() for f in flags]
        assert any("many" in t or "experts" in t for t in terms)

    def test_detects_studies_show(self, detector, config):
        """Test detection of 'studies show' pattern."""
        doc = MockDoc(text="Studies show that people prefer option A.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any("studies" in f.term.lower() for f in flags)

    def test_detects_some_people(self, detector, config):
        """Test detection of 'some people' pattern."""
        doc = MockDoc(text="Some people think this is important.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any("some" in f.term.lower() for f in flags)

    def test_detects_research_suggests(self, detector, config):
        """Test detection of 'research suggests' pattern."""
        doc = MockDoc(text="Research suggests a correlation exists.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0

    def test_cited_claims_not_flagged(self, detector, config):
        """Test that claims with citations are not flagged."""
        doc = MockDoc(text="Many experts believe this (Smith, 2023).")
        flags = detector.detect(doc, config)

        # Should have fewer or no flags due to citation
        weasel_flags = [f for f in flags if f.type == FlagType.WEASEL]
        # The citation should reduce weasel flags
        assert len(weasel_flags) == 0 or not any(
            "many experts" in f.term.lower() for f in weasel_flags
        )

    def test_custom_weasels(self, detector):
        """Test detection of custom weasel patterns."""
        config = Config(additional_weasels=["reportedly", "supposedly"])
        doc = MockDoc(text="The method reportedly works well.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any("reportedly" in f.term.lower() for f in flags)

    def test_case_insensitive(self, detector, config):
        """Test that detection is case insensitive."""
        doc = MockDoc(text="MANY EXPERTS believe this is TRUE.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0

    def test_suggestions_provided(self, detector, config):
        """Test that suggestions are provided for flags."""
        doc = MockDoc(text="Many experts believe this is correct.")
        flags = detector.detect(doc, config)

        for flag in flags:
            assert flag.suggestion is not None
            assert len(flag.suggestion) > 0

    def test_empty_text(self, detector, config):
        """Test that empty text returns no flags."""
        doc = MockDoc(text="")
        flags = detector.detect(doc, config)
        assert len(flags) == 0

    def test_clean_text_no_flags(self, detector, config):
        """Test that text without weasels has no flags."""
        doc = MockDoc(text="The study by Smith (2023) found a 15% improvement.")
        flags = detector.detect(doc, config)
        # Should have no weasel flags since specific citation is provided
        weasel_flags = [f for f in flags if f.type == FlagType.WEASEL]
        assert len(weasel_flags) == 0
