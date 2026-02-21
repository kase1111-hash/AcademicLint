"""Model download and management for AcademicLint."""

import re
import subprocess
from pathlib import Path
from typing import Optional

# Strict allowlist for spaCy model names: language_core_web_size
VALID_MODEL_PATTERN = re.compile(r"^[a-z]{2}_core_web_(sm|md|lg|trf)$")

# Timeout for model download subprocess (5 minutes)
MODEL_DOWNLOAD_TIMEOUT = 300


class ModelManager:
    """Manages NLP model downloads and caching."""

    DEFAULT_MODELS = ["en_core_web_lg"]
    CACHE_DIR = Path.home() / ".cache" / "academiclint" / "models"

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or self.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def validate_model_name(model_name: str) -> None:
        """Validate a model name against the allowlist.

        Args:
            model_name: Name to validate

        Raises:
            ValueError: If the model name doesn't match the expected pattern
        """
        if not isinstance(model_name, str) or not VALID_MODEL_PATTERN.match(model_name):
            raise ValueError(
                f"Invalid model name: {model_name!r}. "
                "Expected format: xx_core_web_(sm|md|lg|trf)"
            )

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

        Raises:
            ValueError: If model_name fails validation
        """
        self.validate_model_name(model_name)

        if not force and self.is_model_installed(model_name):
            return True

        if model_name.startswith("en_core_web"):
            return self._download_spacy_model(model_name)

        return False

    def _download_spacy_model(self, model_name: str) -> bool:
        """Download a spaCy model."""
        try:
            result = subprocess.run(
                ["python", "-m", "spacy", "download", model_name],
                capture_output=True,
                text=True,
                timeout=MODEL_DOWNLOAD_TIMEOUT,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

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
