"""Parametrized real-sentence tests for each detector.

Tests detectors against realistic academic sentences to verify:
- True positives: bad patterns ARE flagged
- True negatives: legitimate academic usage is NOT flagged (or flagged sparingly)

These tests use MockDoc to bypass spaCy, exercising each detector's
regex-based logic directly.
"""

import pytest
from dataclasses import dataclass, field

from academiclint.core.config import Config
from academiclint.core.result import FlagType
from academiclint.detectors.vagueness import VaguenessDetector
from academiclint.detectors.circular import CircularDetector
from academiclint.detectors.causal import CausalDetector
from academiclint.detectors.hedge import HedgeDetector
from academiclint.detectors.weasel import WeaselDetector
from academiclint.detectors.filler import FillerDetector
from academiclint.detectors.citation import CitationDetector


@dataclass
class MockSpan:
    """Minimal span with start/end offsets."""
    start: int
    end: int


@dataclass
class MockSentence:
    """Minimal sentence object with .text and .span attributes."""
    text: str
    span: MockSpan = None

    def __post_init__(self):
        if self.span is None:
            self.span = MockSpan(start=0, end=len(self.text))


@dataclass
class MockDoc:
    """Minimal ProcessedDocument stand-in for detector testing."""
    text: str
    sentences: list = field(default_factory=list)
    paragraphs: list = None

    def __post_init__(self):
        # Auto-populate sentences as MockSentence objects
        if not self.sentences:
            self.sentences = [MockSentence(text=self.text)]

    def get_sentence_for_span(self, start, end):
        """Find the sentence containing a character span."""
        for sent in self.sentences:
            if sent.span.start <= start and end <= sent.span.end:
                return sent
        return None


# ── VaguenessDetector ──────────────────────────────────────────────────

class TestVaguenessRealSentences:

    @pytest.fixture
    def detector(self):
        return VaguenessDetector()

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.mark.parametrize("sentence", [
        "Many things have recently changed in big ways.",
        "The impact of stuff on people is interesting.",
        "Things have changed significantly and are very important.",
        "Some really great stuff happened sometimes.",
    ])
    def test_true_positives(self, detector, config, sentence):
        """Genuinely vague sentences should produce at least one flag."""
        flags = detector.detect(MockDoc(text=sentence), config)
        assert len(flags) >= 1, f"No flags for: {sentence!r}"

    @pytest.mark.parametrize("sentence", [
        "The 34% reduction in response time was statistically significant (p < 0.01).",
        "CRISPR-Cas9 enables precise modification of endogenous genes.",
        "Cox proportional hazards models indicate a 40% reduction.",
        "Functional connectivity within the DMN predicts creative thinking.",
    ])
    def test_true_negatives_low_flag_count(self, detector, config, sentence):
        """Precise academic sentences should produce at most 1 flag."""
        flags = detector.detect(MockDoc(text=sentence), config)
        assert len(flags) <= 1, (
            f"Too many flags ({len(flags)}) for precise sentence: {sentence!r}. "
            f"Flagged: {[f.term for f in flags]}"
        )

    def test_domain_terms_excluded(self, detector):
        """Terms marked as domain vocabulary should not be flagged."""
        config = Config(domain_terms=["impact", "significant"])
        flags = detector.detect(
            MockDoc(text="The impact was significant."), config
        )
        terms = [f.term.lower() for f in flags]
        assert "impact" not in terms
        assert "significant" not in terms


# ── CircularDetector ───────────────────────────────────────────────────

class TestCircularRealSentences:

    @pytest.fixture
    def detector(self):
        return CircularDetector()

    @pytest.fixture
    def config(self):
        return Config()

    def test_true_positive_same_root(self, detector, config):
        """Circular definitions with same stem should be flagged."""
        # The simple stemmer can reduce "freedom" → "free" via -dom suffix
        sentence = "Freedom is the state of being free."
        flags = detector.detect(MockDoc(text=sentence), config)
        circular = [f for f in flags if f.type == FlagType.CIRCULAR]
        assert len(circular) >= 1, f"No circular flag for: {sentence!r}"

    @pytest.mark.parametrize("sentence", [
        "Democracy means a democratic form of government.",
        "Education is the process of educating students.",
    ])
    def test_suffix_variants_detected(self, detector, config, sentence):
        """Morphological variants should be caught by prefix-based root matching."""
        flags = detector.detect(MockDoc(text=sentence), config)
        circular = [f for f in flags if f.type == FlagType.CIRCULAR]
        assert len(circular) >= 1, f"No circular flag for: {sentence!r}"

    @pytest.mark.parametrize("sentence", [
        "Entropy is the measure of disorder in a thermodynamic system.",
        "Epistemic justification is the property of beliefs formed through reliable processes.",
        "A transformer is a neural network architecture using self-attention mechanisms.",
    ])
    def test_true_negatives(self, detector, config, sentence):
        """Non-circular definitions should not be flagged."""
        flags = detector.detect(MockDoc(text=sentence), config)
        circular = [f for f in flags if f.type == FlagType.CIRCULAR]
        assert len(circular) == 0, (
            f"False circular flag for: {sentence!r}. "
            f"Flagged: {[(f.term, f.message) for f in circular]}"
        )


# ── CausalDetector ────────────────────────────────────────────────────

class TestCausalRealSentences:

    @pytest.fixture
    def detector(self):
        return CausalDetector()

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.mark.parametrize("sentence", [
        "Social media causes depression in teenagers.",
        "Video games lead to increased aggression.",
        "Sugar results in hyperactivity in children.",
    ])
    def test_true_positives(self, detector, config, sentence):
        """Unsupported causal claims should be flagged."""
        flags = detector.detect(MockDoc(text=sentence), config)
        causal = [f for f in flags if f.type == FlagType.UNSUPPORTED_CAUSAL]
        assert len(causal) >= 1, f"No causal flag for: {sentence!r}"

    @pytest.mark.parametrize("sentence", [
        "Minimum wage increases lead to reduced teen employment (Dube et al., 2010).",
        "Semaglutide produces sustained weight loss in adults with obesity (Wilding et al., 2021).",
        "Labor scarcity caused by plague raised peasant wages (Hatcher, 1994).",
    ])
    def test_cited_claims_suppressed(self, detector, config, sentence):
        """Causal claims with citations should not be flagged."""
        flags = detector.detect(MockDoc(text=sentence), config)
        causal = [f for f in flags if f.type == FlagType.UNSUPPORTED_CAUSAL]
        assert len(causal) == 0, (
            f"Cited causal claim should not be flagged: {sentence!r}. "
            f"Flagged: {[f.term for f in causal]}"
        )


# ── HedgeDetector ─────────────────────────────────────────────────────

class TestHedgeRealSentences:

    @pytest.fixture
    def detector(self):
        return HedgeDetector()

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.mark.parametrize("sentence", [
        "It may possibly be the case that some outcomes could perhaps tend to occur.",
        "Results arguably might somewhat suggest a relatively likely pattern.",
    ])
    def test_true_positives(self, detector, config, sentence):
        """Hedge-stacked sentences should be flagged."""
        flags = detector.detect(MockDoc(text=sentence), config)
        hedge = [f for f in flags if f.type == FlagType.HEDGE_STACK]
        assert len(hedge) >= 1, f"No hedge flag for: {sentence!r}"

    @pytest.mark.parametrize("sentence", [
        "These findings suggest a trade-off between speed and depth.",
        "The results may indicate a correlation, though causation remains unestablished.",
        "This effect could reflect individual differences in cognitive reflection.",
    ])
    def test_single_hedges_not_flagged(self, detector, config, sentence):
        """Single hedges (normal academic caution) should not be flagged."""
        flags = detector.detect(MockDoc(text=sentence), config)
        hedge = [f for f in flags if f.type == FlagType.HEDGE_STACK]
        assert len(hedge) == 0, (
            f"Single hedge should not be flagged: {sentence!r}. "
            f"Flagged: {[f.term for f in hedge]}"
        )


# ── WeaselDetector ────────────────────────────────────────────────────

class TestWeaselRealSentences:

    @pytest.fixture
    def detector(self):
        return WeaselDetector()

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.mark.parametrize("sentence", [
        "Many experts believe this is important.",
        "It is widely believed that climate change is real.",
        "Research suggests a correlation.",
        "Some studies show positive results.",
    ])
    def test_true_positives(self, detector, config, sentence):
        """Weasel word patterns should be flagged."""
        flags = detector.detect(MockDoc(text=sentence), config)
        weasel = [f for f in flags if f.type == FlagType.WEASEL]
        assert len(weasel) >= 1, f"No weasel flag for: {sentence!r}"

    @pytest.mark.parametrize("sentence", [
        "Some studies (Smith, 2020) show positive results.",
        "Studies show that DMN-FPCN coupling predicts creative thinking (Beaty et al., 2018).",
        "Research demonstrates sustained elevation of fetal hemoglobin (Frangoul et al., 2021).",
    ])
    def test_cited_weasels_suppressed(self, detector, config, sentence):
        """Weasel patterns with citations in the same sentence should not be flagged."""
        flags = detector.detect(MockDoc(text=sentence), config)
        weasel = [f for f in flags if f.type == FlagType.WEASEL]
        assert len(weasel) == 0, (
            f"Cited weasel should not be flagged: {sentence!r}. "
            f"Flagged: {[f.term for f in weasel]}"
        )


# ── FillerDetector ────────────────────────────────────────────────────

class TestFillerRealSentences:

    @pytest.fixture
    def detector(self):
        return FillerDetector()

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.mark.parametrize("sentence,expected_term", [
        ("In today's society, technology is everywhere.", "in today's society"),
        ("It goes without saying that water is essential.", "it goes without saying"),
        ("At the end of the day, results matter.", "at the end of the day"),
        ("It is important to note that errors occurred.", "it is important to note that"),
    ])
    def test_true_positives(self, detector, config, sentence, expected_term):
        """Filler phrases should be flagged."""
        flags = detector.detect(MockDoc(text=sentence), config)
        filler = [f for f in flags if f.type == FlagType.FILLER]
        assert len(filler) >= 1, f"No filler flag for: {sentence!r}"

    @pytest.mark.parametrize("sentence", [
        "We observed a 34% reduction in response time.",
        "The pre-trained model achieves state-of-the-art results.",
        "Functional connectivity was characterized using resting-state fMRI.",
    ])
    def test_true_negatives(self, detector, config, sentence):
        """Precise academic sentences should not trigger filler flags."""
        flags = detector.detect(MockDoc(text=sentence), config)
        filler = [f for f in flags if f.type == FlagType.FILLER]
        assert len(filler) == 0, (
            f"False filler flag for: {sentence!r}. "
            f"Flagged: {[f.term for f in filler]}"
        )


# ── CitationDetector ──────────────────────────────────────────────────

class TestCitationRealSentences:

    @pytest.fixture
    def detector(self):
        return CitationDetector()

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.mark.parametrize("sentence", [
        "Studies show 90% of people prefer option A.",
        "In 2015, everything changed dramatically.",
        "According to experts, this is the largest study.",
    ])
    def test_true_positives(self, detector, config, sentence):
        """Claims needing citations should be flagged when uncited."""
        flags = detector.detect(MockDoc(text=sentence), config)
        citation = [f for f in flags if f.type == FlagType.CITATION_NEEDED]
        assert len(citation) >= 1, f"No citation flag for: {sentence!r}"

    @pytest.mark.parametrize("sentence", [
        "The signal-to-noise ratio was 24 (Abbott et al., 2016).",
        "Participants scored 23% of the time (Toplak et al., 2011).",
        "Real wages rose 40-60% on estates with weak control [1].",
    ])
    def test_cited_claims_not_flagged(self, detector, config, sentence):
        """Properly cited claims should not be flagged."""
        flags = detector.detect(MockDoc(text=sentence), config)
        citation = [f for f in flags if f.type == FlagType.CITATION_NEEDED]
        assert len(citation) == 0, (
            f"Cited claim should not be flagged: {sentence!r}. "
            f"Flagged: {[f.term for f in citation]}"
        )
