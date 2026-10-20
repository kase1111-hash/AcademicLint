"""Tests for the NLP pipeline's spaCy model loading."""

import pytest
import spacy

from academiclint import Linter
from academiclint.core.exceptions import ModelLoadError, ModelNotFoundError, ProcessingError
from academiclint.core.parser import CITATION_PLACEHOLDER
from academiclint.core.pipeline import DEFAULT_MODEL, NLPPipeline
from academiclint.core.result import FlagType


def fake_load(installed):
    """Build a spacy.load stand-in where only `installed` models exist."""

    def load(name, *args, **kwargs):
        if name not in installed:
            raise OSError(f"[E050] Can't find model '{name}'")
        return spacy.blank("en")

    return load


class TestModelLoading:
    """Tests for choosing which spaCy model to load."""

    def test_prefers_default_model(self, monkeypatch):
        """The large model is used when it is installed."""
        monkeypatch.setattr(spacy, "load", fake_load({"en_core_web_lg", "en_core_web_sm"}))
        pipeline = NLPPipeline()
        pipeline._ensure_loaded()

        assert pipeline.model_name == DEFAULT_MODEL

    def test_falls_back_to_smaller_model(self, monkeypatch):
        """Without the large model, an installed smaller model is used."""
        monkeypatch.setattr(spacy, "load", fake_load({"en_core_web_sm"}))
        pipeline = NLPPipeline()
        pipeline._ensure_loaded()

        assert pipeline.model_name == "en_core_web_sm"

    def test_no_model_installed_raises(self, monkeypatch):
        """With no model installed, the error names the default model."""
        monkeypatch.setattr(spacy, "load", fake_load(set()))

        with pytest.raises(ModelNotFoundError) as exc_info:
            NLPPipeline()._ensure_loaded()
        assert exc_info.value.model_name == DEFAULT_MODEL

    def test_broken_model_raises_model_load_error(self, monkeypatch):
        """A load failure is a ModelLoadError, still catchable as ProcessingError."""

        def broken_load(name, *args, **kwargs):
            raise RuntimeError("corrupt model")

        monkeypatch.setattr(spacy, "load", broken_load)

        with pytest.raises(ModelLoadError) as exc_info:
            NLPPipeline()._ensure_loaded()
        assert isinstance(exc_info.value, ProcessingError)

    def test_explicit_model_does_not_fall_back(self, monkeypatch):
        """A model requested by name must be that model, not a substitute."""
        monkeypatch.setattr(spacy, "load", fake_load({"en_core_web_sm"}))

        with pytest.raises(ModelNotFoundError) as exc_info:
            NLPPipeline("en_core_web_md")._ensure_loaded()
        assert exc_info.value.model_name == "en_core_web_md"


class TestSentenceSplitting:
    """Tests for sentence boundaries at paragraph breaks (uses the installed model)."""

    HEADED = "Methods\n\nJohnson (2019) found that sleep deprivation causes memory loss."

    def test_heading_split_from_body_sentence(self):
        """A heading becomes its own sentence and the body sentence stays whole."""
        doc = NLPPipeline().process(self.HEADED)

        assert [s.text for s in doc.sentences] == [
            "Methods",
            "Johnson (2019) found that sleep deprivation causes memory loss.",
        ]

    def test_citation_stays_with_its_claim(self):
        """Splitting the body sentence would detach the citation from its claim."""
        result = Linter().check(self.HEADED)

        assert not [f for f in result.flags if f.type == FlagType.UNSUPPORTED_CAUSAL]


def presplit(*parts, sep=" "):
    """A Doc of the joined parts, with a sentence starting at each part.

    Stands in for a parser's sentence boundaries, so the boundaries of a
    particular model (e.g. the large one) can be tested with any model.
    """
    doc = spacy.blank("en")(sep.join(parts))
    starts, offset = set(), 0
    for part in parts:
        starts.add(offset)
        offset += len(part) + len(sep)
    for token in doc:
        token.is_sent_start = token.idx in starts
    return doc


class TestCitationSplitOff:
    """A citation the parser splits off its claim is merged back into it."""

    @staticmethod
    def sentences(doc):
        return [span.text.strip() for span in NLPPipeline._sentence_spans(doc)]

    @pytest.mark.parametrize(
        "citation", ["[12].", f"{CITATION_PLACEHOLDER}.", "[Smith 2019].", "[1, 2]."]
    )
    def test_citation_only_sentence(self, citation):
        doc = presplit("Studies show that sleep loss impairs recall", citation)

        assert self.sentences(doc) == [f"Studies show that sleep loss impairs recall {citation}"]

    def test_sentence_continuing_after_citation(self):
        doc = presplit("Many experts agree that sleep matters", "[12], and others agree.")

        assert self.sentences(doc) == [
            "Many experts agree that sleep matters [12], and others agree."
        ]

    def test_citation_opening_a_new_sentence(self):
        doc = presplit("It is known.", "[12] Many experts agree.")

        assert self.sentences(doc) == ["It is known.", "[12] Many experts agree."]

    def test_citation_only_on_the_next_line(self):
        doc = presplit("Studies show that sleep loss impairs recall", "[12].", sep="\n")

        assert self.sentences(doc) == ["Studies show that sleep loss impairs recall\n[12]."]

    def test_citation_opening_a_wrapped_line(self):
        """Hard-wrapped prose often breaks the line just before a citation."""
        doc = presplit("Sleep loss impairs recall", "[12], at least in adults.", sep="\n")

        assert self.sentences(doc) == ["Sleep loss impairs recall\n[12], at least in adults."]

    def test_split_at_sentence_start(self):
        """A given start (a list item) splits a sentence the parser ran on."""
        text = "It is widely believed that screen time causes insomnia\n[4] found no effect"
        doc = presplit(text)

        spans = NLPPipeline._sentence_spans(doc, [text.index("[4]") - 1])

        assert [span.text.strip() for span in spans] == [
            "It is widely believed that screen time causes insomnia",
            "[4] found no effect",
        ]

    def test_no_citation_merge_at_sentence_start(self):
        doc = presplit("Studies show that sleep loss impairs recall", "[12].", sep="\n")

        spans = NLPPipeline._sentence_spans(doc, [doc.text.index("[12]")])

        assert len(spans) == 2

    def test_split_after_cited_sentence_end(self):
        """A LaTeX citation ending a sentence ends it, whatever the parser says."""
        doc = presplit(
            f"Later accounts stress local elites {CITATION_PLACEHOLDER}.\n"
            "Research shows that most petitions were rural."
        )

        assert self.sentences(doc) == [
            f"Later accounts stress local elites {CITATION_PLACEHOLDER}.",
            "Research shows that most petitions were rural.",
        ]

    def test_reminder_does_not_chain_merges(self):
        """A reminder after a full stop joins its claim, but the next sentence doesn't."""
        doc = presplit(
            "Most experts agree that naps help.", "[citation needed]", "[12] found more."
        )

        assert self.sentences(doc) == [
            "Most experts agree that naps help. [citation needed]",
            "[12] found more.",
        ]

    @staticmethod
    def tagged(*parts, **tags):
        """presplit() with the given (pos, tag) set on words, as a tagger would."""
        doc = presplit(*parts, sep="\n")
        for token in doc:
            if token.text in tags:
                token.pos_, token.tag_ = tags[token.text]
        return doc

    def test_citation_leading_a_clause_on_the_next_line(self):
        """In an outline, "[3] reported..." on its own line starts a new statement."""
        doc = self.tagged(
            "Most students procrastinate weekly",
            "[3] reported that it helps.",
            procrastinate=("VERB", "VBP"),
            reported=("VERB", "VBD"),
        )

        assert len(self.sentences(doc)) == 2

    @pytest.mark.parametrize(
        ("claim", "rest", "tags"),
        [
            # A participle after the citation carries on the sentence
            (
                "Working memory predicts reading in children",
                "[21] suggesting that it matters.",
                {"predicts": ("VERB", "VBZ"), "suggesting": ("VERB", "VBG")},
            ),
            # A subject without a verb of its own takes the citation with it
            ("Many researchers", "[12] argue that it matters.", {"argue": ("VERB", "VBP")}),
            (
                "Although it is unclear, many researchers",
                "[12] argue that it matters.",
                {"is": ("AUX", "VBZ"), "argue": ("VERB", "VBP")},
            ),
        ],
    )
    def test_citation_carrying_on_the_line_before(self, claim, rest, tags):
        doc = self.tagged(claim, rest, **tags)

        assert len(self.sentences(doc)) == 1

    def test_reminder_inside_a_sentence(self):
        doc = presplit("Transformers outperform baselines", "[citation needed] on benchmarks.")

        assert self.sentences(doc) == [
            "Transformers outperform baselines [citation needed] on benchmarks."
        ]

    def test_split_after_bracketed_sentence_end(self):
        """A reminder or citation, a full stop and a capital end the sentence."""
        doc = presplit("Naps help [citation needed].\nMednick (2003) found more.")
        line_end = presplit("Studies show that naps help\n[citation needed]\nExperts agree [12].")

        assert self.sentences(doc) == ["Naps help [citation needed].", "Mednick (2003) found more."]
        # Not after a citation: the next word is often a name
        cited = presplit("As reported in [12]\nSmith et al. showed that most recovered.")
        assert len(self.sentences(cited)) == 1
        assert self.sentences(line_end) == [
            "Studies show that naps help\n[citation needed]",
            "Experts agree [12].",
        ]

    def test_citation_after_a_blank_line(self):
        doc = presplit("Introduction", "[12].", sep="\n\n")

        assert self.sentences(doc) == ["Introduction", "[12]."]
