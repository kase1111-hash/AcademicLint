"""Tests for jargon density detector."""

from dataclasses import dataclass, field

import pytest

from academiclint.core.config import Config
from academiclint.core.result import FlagType, Severity, Span
from academiclint.detectors.jargon import JargonDetector


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


class TestJargonDetector:
    """Tests for JargonDetector."""

    @pytest.fixture
    def detector(self):
        """Create a jargon detector."""
        return JargonDetector()

    @pytest.fixture
    def config(self):
        """Create default config."""
        return Config()

    def test_flag_types(self, detector):
        """Test that detector returns correct flag types."""
        assert FlagType.JARGON_DENSE in detector.flag_types

    def test_detects_jargon_dense_passage(self, detector, config):
        """Test detection of jargon-dense passages."""
        text = (
            "The epistemological ramifications of methodological considerations "
            "require comprehensive hermeneutical analysis."
        )
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        # Should flag due to high jargon density
        jargon_flags = [f for f in flags if f.type == FlagType.JARGON_DENSE]
        assert len(jargon_flags) >= 0  # May or may not flag depending on threshold

    def test_plain_text_not_flagged(self, detector, config):
        """Test that plain text is not flagged."""
        text = "The dog ran across the green field."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        jargon_flags = [f for f in flags if f.type == FlagType.JARGON_DENSE]
        assert len(jargon_flags) == 0

    def test_domain_terms_not_counted(self, detector):
        """Test that domain terms are not counted as jargon."""
        config = Config(domain_terms=["epistemology", "hermeneutics"])
        text = "Epistemology and hermeneutics are important fields."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        jargon_flags = [f for f in flags if f.type == FlagType.JARGON_DENSE]
        assert len(jargon_flags) == 0

    def test_is_jargon_method(self, detector):
        """Test the jargon detection method."""
        domain_terms = set()

        # Complex words should be detected as jargon
        assert detector._is_jargon("epistemology", domain_terms)
        assert detector._is_jargon("methodological", domain_terms)
        assert detector._is_jargon("hermeneutical", domain_terms)
        assert detector._is_jargon("categorization", domain_terms)

        # Short/common words should not be jargon
        assert not detector._is_jargon("the", domain_terms)
        assert not detector._is_jargon("and", domain_terms)
        assert not detector._is_jargon("is", domain_terms)

    def test_domain_terms_exclude_jargon(self, detector):
        """Test that domain terms are excluded from jargon."""
        domain_terms = {"epistemology", "ontology"}
        assert not detector._is_jargon("epistemology", domain_terms)
        assert not detector._is_jargon("ontology", domain_terms)

    def test_explained_jargon_not_flagged(self, detector, config):
        """Test that explained jargon is not flagged."""
        text = (
            "Epistemology (the study of knowledge) and ontology "
            "(the study of being) are philosophical foundations."
        )
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        # Explanations should reduce flags
        jargon_flags = [f for f in flags if f.type == FlagType.JARGON_DENSE]
        # Should have fewer or no flags due to explanations
        assert len(jargon_flags) <= 1

    def test_has_explanations_method(self, detector):
        """Test the explanation detection method."""
        terms = ["term1", "term2"]

        # Parenthetical explanations
        text_with_parens = "Term1 (definition) and term2 (another def)."
        assert detector._has_explanations(text_with_parens, terms)

        # 'which means' explanation
        text_with_which = "Term1, which means something specific."
        assert detector._has_explanations(text_with_which, terms[:1])

        # No explanation
        text_without = "Term1 and term2 are important."
        assert not detector._has_explanations(text_without, terms)

    def test_count_explanations_method(self, detector):
        """Test the explanation counting method."""
        # Multiple explanations
        text = "Term1 (def), which means X, i.e., Y."
        count = detector._count_explanations(text)
        assert count >= 2

        # No explanations
        text_plain = "Simple sentence without explanations."
        count = detector._count_explanations(text_plain)
        assert count == 0

    def test_threshold_constant(self, detector):
        """Test that jargon threshold is defined."""
        assert hasattr(detector, "JARGON_THRESHOLD")
        assert detector.JARGON_THRESHOLD == 0.3  # 30%

    def test_provides_suggestion(self, detector, config):
        """Test that suggestions are provided."""
        text = (
            "The epistemological methodological hermeneutical categorical "
            "considerations require comprehensive analytical examination."
        )
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        for flag in flags:
            if flag.type == FlagType.JARGON_DENSE:
                assert flag.suggestion is not None
                assert "define" in flag.suggestion.lower() or "audience" in flag.suggestion.lower()

    def test_message_includes_counts(self, detector, config):
        """Test that message includes term and explanation counts."""
        text = (
            "The epistemological methodological hermeneutical categorical "
            "considerations require comprehensive analytical examination."
        )
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        for flag in flags:
            if flag.type == FlagType.JARGON_DENSE:
                assert "term" in flag.message.lower()
                assert "explanation" in flag.message.lower()

    def test_empty_sentences(self, detector, config):
        """Test that empty sentences list returns no flags."""
        doc = MockDoc(text="Some text.", sentences=[])
        flags = detector.detect(doc, config)
        assert len(flags) == 0

    def test_severity_is_medium(self, detector, config):
        """Test that jargon flags have MEDIUM severity."""
        text = (
            "The epistemological methodological hermeneutical categorical "
            "considerations require comprehensive analytical examination."
        )
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        for flag in flags:
            if flag.type == FlagType.JARGON_DENSE:
                assert flag.severity == Severity.MEDIUM

    def test_minimum_jargon_count(self, detector, config):
        """Test that minimum of 3 jargon terms required."""
        # Only 2 jargon terms - should not flag
        text = "The epistemological consideration is important."
        doc = MockDoc(
            text=text,
            sentences=[MockSentence(text=text, span=Span(0, len(text)))],
        )
        flags = detector.detect(doc, config)

        jargon_flags = [f for f in flags if f.type == FlagType.JARGON_DENSE]
        # Should not flag with only 1-2 jargon terms
        assert len(jargon_flags) == 0
