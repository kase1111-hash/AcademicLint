"""Tests for the NLP pipeline's spaCy model loading."""

import pytest
import spacy

from academiclint import Linter
from academiclint.core.exceptions import ModelLoadError, ModelNotFoundError, ProcessingError
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
        """A model that is installed but fails to load is not a ProcessingError."""

        def broken_load(name, *args, **kwargs):
            raise RuntimeError("corrupt model")

        monkeypatch.setattr(spacy, "load", broken_load)

        with pytest.raises(ModelLoadError) as exc_info:
            NLPPipeline()._ensure_loaded()
        assert not isinstance(exc_info.value, ProcessingError)

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
