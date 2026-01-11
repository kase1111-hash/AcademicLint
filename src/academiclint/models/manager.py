"""Model download and management for AcademicLint."""

from pathlib import Path
from typing import Optional


class ModelManager:
    """Manages NLP model downloads and caching."""

    DEFAULT_MODELS = ["en_core_web_lg"]
    CACHE_DIR = Path.home() / ".cache" / "academiclint" / "models"

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or self.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def is_model_installed(self, model_name: str) -> bool:
        """Check if a model is installed.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model is installed
        """
        if model_name.startswith("en_core_web"):
            try:
                import spacy

                spacy.load(model_name)
                return True
            except OSError:
                return False
        return False

    def download_model(self, model_name: str, force: bool = False) -> bool:
        """Download a model.

        Args:
            model_name: Name of the model to download
            force: Re-download even if exists

        Returns:
            True if download succeeded
        """
        if not force and self.is_model_installed(model_name):
            return True

        if model_name.startswith("en_core_web"):
            return self._download_spacy_model(model_name)

        return False

    def _download_spacy_model(self, model_name: str) -> bool:
        """Download a spaCy model."""
        import subprocess

        result = subprocess.run(
            ["python", "-m", "spacy", "download", model_name],
            capture_output=True,
            text=True,
        )

        return result.returncode == 0

    def ensure_models(self, models: Optional[list[str]] = None) -> bool:
        """Ensure required models are installed.

        Args:
            models: List of model names, or None for defaults

        Returns:
            True if all models are installed
        """
        models = models or self.DEFAULT_MODELS

        all_installed = True
        for model in models:
            if not self.is_model_installed(model):
                if not self.download_model(model):
                    all_installed = False

        return all_installed

    def list_installed_models(self) -> list[str]:
        """List installed models.

        Returns:
            List of installed model names
        """
        installed = []

        for model in self.DEFAULT_MODELS:
            if self.is_model_installed(model):
                installed.append(model)

        return installed
