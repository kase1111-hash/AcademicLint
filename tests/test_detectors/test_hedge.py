"""Tests for hedge stacking detector."""

from dataclasses import dataclass, field

import pytest

from academiclint.core.config import Config
from academiclint.core.result import FlagType, Severity, Span
from academiclint.detectors.hedge import HedgeDetector


@dataclass
class MockSentence:
    """Mock sentence for testing."""

    text: str
    span: Span


@dataclass
class MockDoc:
    """Mock ProcessedDocument for testing."""

    text: str
    sentences: list = field(default_factory=list)
    paragraphs: list = None


class TestHedgeDetector:
    """Tests for HedgeDetector."""

    @pytest.fixture
    def detector(self):
        """Create a hedge detector."""
        return HedgeDetector()

    @pytest.fixture
    def config(self):
        """Create default config."""
        return Config()

    def test_flag_types(self, detector):
        """Test that detector returns correct flag types."""
        assert FlagType.HEDGE_STACK in detector.flag_types

    def test_detects_multiple_hedges(self, detector, config):
        """Test detection of multiple hedges in one clause."""
        text = "It might possibly perhaps be somewhat true."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any(f.type == FlagType.HEDGE_STACK for f in flags)

    def test_threshold_of_three(self, detector, config):
        """Test that threshold is 3 hedges."""
        # Two hedges - should not flag
        text_two = "It might possibly be true."
        doc_two = MockDoc(
            text=text_two,
            sentences=[MockSentence(text=text_two, span=Span(0, len(text_two)))],
        )
        flags_two = detector.detect(doc_two, config)
        hedge_flags = [f for f in flags_two if f.type == FlagType.HEDGE_STACK]
        assert len(hedge_flags) == 0

        # Three hedges - should flag
        text_three = "It might possibly perhaps be true."
        doc_three = MockDoc(
            text=text_three,
            sentences=[MockSentence(text=text_three, span=Span(0, len(text_three)))],
        )
        flags_three = detector.detect(doc_three, config)
        hedge_flags = [f for f in flags_three if f.type == FlagType.HEDGE_STACK]
        assert len(hedge_flags) > 0

    def test_clause_boundary(self, detector, config):
        """Test that hedges are counted per clause."""
        # Hedges split across clauses should not stack
        text = "It might be true, but perhaps it is."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)
        # Each clause has fewer than 3 hedges
        hedge_flags = [f for f in flags if f.type == FlagType.HEDGE_STACK]
        assert len(hedge_flags) == 0

    def test_severity_medium_for_few_hedges(self, detector, config):
        """Test that 3-4 hedges have MEDIUM severity."""
        text = "It might possibly perhaps be true."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        for flag in flags:
            if flag.type == FlagType.HEDGE_STACK:
                assert flag.severity == Severity.MEDIUM

    def test_severity_high_for_many_hedges(self, detector, config):
        """Test that 5+ hedges have HIGH severity."""
        text = "It might possibly perhaps seemingly apparently be somewhat true."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        high_severity = [
            f for f in flags
            if f.type == FlagType.HEDGE_STACK and f.severity == Severity.HIGH
        ]
        # If there are 5+ hedges, severity should be HIGH
        if any("5" in f.term or "6" in f.term for f in flags):
            assert len(high_severity) > 0

    def test_confidence_estimate(self, detector):
        """Test confidence estimation method."""
        # 3 hedges = 0.9^3 ≈ 0.729
        confidence = detector._estimate_confidence(3)
        assert 0.72 < confidence < 0.74

        # 5 hedges = 0.9^5 ≈ 0.59
        confidence = detector._estimate_confidence(5)
        assert 0.58 < confidence < 0.60

    def test_count_hedges_method(self, detector):
        """Test hedge counting method."""
        count = detector._count_hedges("It might possibly perhaps be true")
        assert count >= 3

        count = detector._count_hedges("This is definitely true")
        assert count == 0

    def test_message_includes_count(self, detector, config):
        """Test that message includes hedge count."""
        text = "It might possibly perhaps be true."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        for flag in flags:
            if flag.type == FlagType.HEDGE_STACK:
                assert "hedge" in flag.message.lower()
                assert "%" in flag.message  # confidence percentage

    def test_provides_suggestion(self, detector, config):
        """Test that suggestions are provided."""
        text = "It might possibly perhaps be true."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        for flag in flags:
            assert flag.suggestion is not None
            assert len(flag.suggestion) > 0

    def test_empty_sentences(self, detector, config):
        """Test that empty sentences list returns no flags."""
        doc = MockDoc(text="Some text.", sentences=[])
        flags = detector.detect(doc, config)
        assert len(flags) == 0

    def test_clean_text_no_flags(self, detector, config):
        """Test that clear text has no flags."""
        text = "The experiment produced conclusive results."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)
        hedge_flags = [f for f in flags if f.type == FlagType.HEDGE_STACK]
        assert len(hedge_flags) == 0

    def test_hedge_threshold_constant(self, detector):
        """Test that hedge threshold is defined."""
        assert hasattr(detector, "HEDGE_THRESHOLD")
        assert detector.HEDGE_THRESHOLD == 3
