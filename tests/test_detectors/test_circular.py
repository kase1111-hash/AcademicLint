"""Tests for circular definition detector."""

from dataclasses import dataclass, field

import pytest

from academiclint.core.config import Config
from academiclint.core.result import FlagType, Severity, Span
from academiclint.detectors.circular import CircularDetector


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

    def get_sentence_for_span(self, start, end):
        for sent in self.sentences:
            if hasattr(sent, 'span') and sent.span.start <= start and end <= sent.span.end:
                return sent
        return None


class TestCircularDetector:
    """Tests for CircularDetector."""

    @pytest.fixture
    def detector(self):
        """Create a circular definition detector."""
        return CircularDetector()

    @pytest.fixture
    def config(self):
        """Create default config."""
        return Config()

    def test_flag_types(self, detector):
        """Test that detector returns correct flag types."""
        assert FlagType.CIRCULAR in detector.flag_types

    def test_detects_direct_circular(self, detector, config):
        """Test detection of direct circular definition."""
        text = "Freedom is the state of being free."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any(f.type == FlagType.CIRCULAR for f in flags)
        assert any("freedom" in f.term.lower() for f in flags)

    def test_detects_suffix_circular(self, detector, config):
        """Test detection of circular with suffix variation."""
        text = "Democracy means a democratic form of government."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any("democracy" in f.term.lower() for f in flags)

    def test_detects_refers_to_pattern(self, detector, config):
        """Test detection with 'refers to' pattern."""
        text = "Justice refers to a just system."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        assert len(flags) > 0

    def test_non_circular_not_flagged(self, detector, config):
        """Test that non-circular definitions are not flagged."""
        text = "Democracy is a system where citizens vote to select representatives."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        circular_flags = [f for f in flags if f.type == FlagType.CIRCULAR]
        assert len(circular_flags) == 0

    def test_severity_is_high(self, detector, config):
        """Test that circular definitions have HIGH severity."""
        text = "Freedom is the state of being free."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        for flag in flags:
            assert flag.severity == Severity.HIGH

    def test_provides_suggestion(self, detector, config):
        """Test that suggestions are provided."""
        text = "Freedom is the state of being free."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        for flag in flags:
            assert flag.suggestion is not None
            assert len(flag.suggestion) > 0

    def test_provides_example_revision(self, detector, config):
        """Test that example revisions are provided for known terms."""
        text = "Freedom is the state of being free."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        for flag in flags:
            if "freedom" in flag.term.lower():
                assert flag.example_revision is not None

    def test_multiple_sentences(self, detector, config):
        """Test detection across multiple sentences."""
        text = "Freedom is being free. Justice refers to a just system."
        sentences = [
            MockSentence(text="Freedom is being free.", span=Span(0, 22)),
            MockSentence(text="Justice refers to a just system.", span=Span(23, 56)),
        ]
        doc = MockDoc(text=text, sentences=sentences)
        flags = detector.detect(doc, config)

        # Should detect both circular definitions
        assert len(flags) >= 2

    def test_empty_sentences(self, detector, config):
        """Test that empty sentences list returns no flags."""
        doc = MockDoc(text="Some text.", sentences=[])
        flags = detector.detect(doc, config)
        assert len(flags) == 0

    def test_get_root_method(self, detector):
        """Test the root extraction method."""
        assert detector._get_root("democratic") == "democr"
        assert detector._get_root("freedom") == "fre"  # removes 'dom', then trailing 'e'
        assert detector._get_root("running") == "runn"
        assert detector._get_root("happiness") == "happi"

    def test_case_insensitive(self, detector, config):
        """Test that detection is case insensitive."""
        text = "FREEDOM is the state of being FREE."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        assert len(flags) > 0
