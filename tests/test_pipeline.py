"""Tests for the NLP pipeline's spaCy model loading."""

import pytest
import spacy

from academiclint.core.exceptions import ModelNotFoundError
from academiclint.core.pipeline import DEFAULT_MODEL, PARAGRAPH_COMPONENT, NLPPipeline


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

    def test_explicit_model_does_not_fall_back(self, monkeypatch):
        """A model requested by name must be that model, not a substitute."""
        monkeypatch.setattr(spacy, "load", fake_load({"en_core_web_sm"}))

        with pytest.raises(ModelNotFoundError) as exc_info:
            NLPPipeline("en_core_web_md")._ensure_loaded()
        assert exc_info.value.model_name == "en_core_web_md"

    def test_adds_paragraph_boundary_component(self, monkeypatch):
        """The loaded model splits sentences at paragraph breaks."""
        monkeypatch.setattr(spacy, "load", fake_load({"en_core_web_sm"}))
        pipeline = NLPPipeline()
        pipeline._ensure_loaded()

        assert PARAGRAPH_COMPONENT in pipeline._nlp.pipe_names
