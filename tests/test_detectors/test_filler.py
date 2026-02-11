"""Tests for filler phrase detector."""

from dataclasses import dataclass

import pytest

from academiclint.core.config import Config
from academiclint.core.result import FlagType
from academiclint.detectors.filler import FillerDetector


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


class TestFillerDetector:
    """Tests for FillerDetector."""

    @pytest.fixture
    def detector(self):
        """Create a filler detector."""
        return FillerDetector()

    @pytest.fixture
    def config(self):
        """Create default config."""
        return Config()

    def test_flag_types(self, detector):
        """Test that detector returns correct flag types."""
        assert FlagType.FILLER in detector.flag_types

    def test_detects_in_todays_society(self, detector, config):
        """Test detection of 'in today's society' filler."""
        doc = MockDoc(text="In today's society, people use smartphones.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        terms = [f.term.lower() for f in flags]
        assert any("today's society" in t for t in terms)

    def test_detects_it_is_important(self, detector, config):
        """Test detection of 'it is important to note that' filler."""
        doc = MockDoc(text="It is important to note that results vary.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any("important to note" in f.term.lower() for f in flags)

    def test_detects_needless_to_say(self, detector, config):
        """Test detection of 'needless to say' filler."""
        doc = MockDoc(text="Needless to say, this is significant.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any("needless to say" in f.term.lower() for f in flags)

    def test_detects_throughout_history(self, detector, config):
        """Test detection of 'throughout history' filler."""
        doc = MockDoc(text="Throughout history, humans have evolved.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any("throughout history" in f.term.lower() for f in flags)

    def test_detects_at_the_end_of_the_day(self, detector, config):
        """Test detection of 'at the end of the day' filler."""
        doc = MockDoc(text="At the end of the day, results matter.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any("at the end of the day" in f.term.lower() for f in flags)

    def test_detects_in_order_to(self, detector, config):
        """Test detection of 'in order to' filler."""
        doc = MockDoc(text="We need to study in order to learn.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any("in order to" in f.term.lower() for f in flags)

    def test_detects_the_fact_that(self, detector, config):
        """Test detection of 'the fact that' filler."""
        doc = MockDoc(text="The fact that people disagree is normal.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any("the fact that" in f.term.lower() for f in flags)

    def test_case_insensitive(self, detector, config):
        """Test that detection is case insensitive."""
        doc = MockDoc(text="IN TODAY'S SOCIETY, things have changed.")
        flags = detector.detect(doc, config)

        assert len(flags) > 0

    def test_severity_is_low(self, detector, config):
        """Test that filler flags have LOW severity."""
        doc = MockDoc(text="In today's society, things are different.")
        flags = detector.detect(doc, config)

        for flag in flags:
            from academiclint.core.result import Severity
            assert flag.severity == Severity.LOW

    def test_suggestions_provided(self, detector, config):
        """Test that specific suggestions are provided."""
        doc = MockDoc(text="In order to understand, we must study.")
        flags = detector.detect(doc, config)

        for flag in flags:
            assert flag.suggestion is not None
            # 'in order to' should suggest replacing with 'to'
            if "in order to" in flag.term.lower():
                assert "to" in flag.suggestion.lower()

    def test_empty_text(self, detector, config):
        """Test that empty text returns no flags."""
        doc = MockDoc(text="")
        flags = detector.detect(doc, config)
        assert len(flags) == 0

    def test_clean_text_no_flags(self, detector, config):
        """Test that text without fillers has no flags."""
        doc = MockDoc(text="The experiment measured reaction times.")
        flags = detector.detect(doc, config)
        filler_flags = [f for f in flags if f.type == FlagType.FILLER]
        assert len(filler_flags) == 0

    def test_multiple_fillers(self, detector, config):
        """Test detection of multiple fillers in same text."""
        doc = MockDoc(
            text="In today's society, it is important to note that "
            "needless to say, things have changed."
        )
        flags = detector.detect(doc, config)

        # Should detect multiple fillers
        assert len(flags) >= 2

    def test_suggestion_class_constant(self, detector):
        """Test that suggestions dictionary is defined."""
        assert hasattr(detector, "SUGGESTIONS")
        assert isinstance(detector.SUGGESTIONS, dict)
        assert "in today's society" in detector.SUGGESTIONS
