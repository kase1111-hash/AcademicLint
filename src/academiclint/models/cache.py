"""Model caching utilities for AcademicLint."""

from pathlib import Path
from typing import Optional


class ModelCache:
    """Handles caching of loaded models."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".cache" / "academiclint"
        self._loaded_models = {}

    def get(self, model_name: str):
        """Get a cached model.

        Args:
            model_name: Name of the model

        Returns:
            Cached model or None
        """
        return self._loaded_models.get(model_name)

    def put(self, model_name: str, model) -> None:
        """Cache a loaded model.

        Args:
            model_name: Name of the model
            model: The loaded model object
        """
        self._loaded_models[model_name] = model

    def clear(self) -> None:
        """Clear all cached models."""
        self._loaded_models.clear()

    def get_cache_path(self, model_name: str) -> Path:
        """Get the cache path for a model.

        Args:
            model_name: Name of the model

        Returns:
            Path to the model cache directory
        """
        return self.cache_dir / "models" / model_name
