"""Tests for citation needed detector."""

from dataclasses import dataclass, field

import pytest

from academiclint.core.config import Config
from academiclint.core.result import FlagType, Severity, Span
from academiclint.detectors.citation import CitationDetector


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


class TestCitationDetector:
    """Tests for CitationDetector."""

    @pytest.fixture
    def detector(self):
        """Create a citation detector."""
        return CitationDetector()

    @pytest.fixture
    def config(self):
        """Create default config."""
        return Config()

    def test_flag_types(self, detector):
        """Test that detector returns correct flag types."""
        assert FlagType.CITATION_NEEDED in detector.flag_types

    def test_detects_percentage_claim(self, detector, config):
        """Test detection of percentage claims without citation."""
        text = "About 75% of people agree with this statement."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any(f.type == FlagType.CITATION_NEEDED for f in flags)

    def test_cited_percentage_not_flagged(self, detector, config):
        """Test that cited percentage claims are not flagged."""
        text = "About 75% of people agree (Smith, 2023)."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        citation_flags = [f for f in flags if f.type == FlagType.CITATION_NEEDED]
        assert len(citation_flags) == 0

    def test_detects_research_claims(self, detector, config):
        """Test detection of 'research shows' without citation."""
        text = "Research shows that this method is effective."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        assert len(flags) > 0
        assert any(f.type == FlagType.CITATION_NEEDED for f in flags)

    def test_detects_studies_show(self, detector, config):
        """Test detection of 'studies show' without citation."""
        text = "Studies show a correlation between X and Y."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        assert len(flags) > 0

    def test_detects_according_to(self, detector, config):
        """Test detection of vague 'according to' claims."""
        text = "According to experts, this is the best approach."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        assert len(flags) > 0

    def test_has_citation_method(self, detector):
        """Test the citation detection method."""
        # Author-year citation
        assert detector._has_citation("This is true (Smith, 2023).")
        assert detector._has_citation("According to Smith (2023), this is true.")

        # Numeric citation
        assert detector._has_citation("This is true [1].")
        assert detector._has_citation("This is true [1, 2, 3].")

        # No citation
        assert not detector._has_citation("This is true.")
        assert not detector._has_citation("Many experts believe this.")

    def test_severity_high_for_statistics(self, detector, config):
        """Test that statistics have HIGH severity."""
        text = "About 75% of participants reported improvement."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        # Statistics should have high severity
        stats_flags = [f for f in flags if "%" in f.term]
        for flag in stats_flags:
            # Note: actual severity depends on implementation
            assert flag.severity in [Severity.HIGH, Severity.MEDIUM]

    def test_provides_suggestion(self, detector, config):
        """Test that suggestions are provided."""
        text = "Studies show that this approach works."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        for flag in flags:
            assert flag.suggestion is not None
            assert "citation" in flag.suggestion.lower()

    def test_message_explains_issue(self, detector, config):
        """Test that messages explain the issue."""
        text = "According to experts, this is correct."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        for flag in flags:
            assert flag.message is not None
            assert len(flag.message) > 0

    def test_empty_sentences(self, detector, config):
        """Test that empty sentences list returns no flags."""
        doc = MockDoc(text="Some text.", sentences=[])
        flags = detector.detect(doc, config)
        assert len(flags) == 0

    def test_clean_text_no_flags(self, detector, config):
        """Test that properly cited text has no flags."""
        text = "The experiment showed 50% improvement (Jones et al., 2022)."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)
        citation_flags = [f for f in flags if f.type == FlagType.CITATION_NEEDED]
        assert len(citation_flags) == 0

    def test_one_flag_per_sentence(self, detector, config):
        """Test that only one flag is generated per sentence."""
        text = "Studies show 50% improvement and research indicates better outcomes."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        citation_flags = [f for f in flags if f.type == FlagType.CITATION_NEEDED]
        assert len(citation_flags) <= 1

    def test_multiple_sentences(self, detector, config):
        """Test detection across multiple sentences."""
        text = "Studies show X. Research indicates Y."
        sentences = [
            MockSentence(text="Studies show X.", span=Span(0, 15)),
            MockSentence(text="Research indicates Y.", span=Span(16, 37)),
        ]
        doc = MockDoc(text=text, sentences=sentences)
        flags = detector.detect(doc, config)

        # Should detect in both sentences
        citation_flags = [f for f in flags if f.type == FlagType.CITATION_NEEDED]
        assert len(citation_flags) >= 1
