"""Base detector interface for AcademicLint."""

from abc import ABC, abstractmethod

from academiclint.core.config import Config
from academiclint.core.pipeline import ProcessedDocument
from academiclint.core.result import Flag, FlagType


class Detector(ABC):
    """Base class for all detectors."""

    @abstractmethod
    def detect(self, doc: ProcessedDocument, config: Config) -> list[Flag]:
        """Detect issues in the processed document.

        Args:
            doc: NLP-processed document
            config: Linter configuration

        Returns:
            List of detected flags
        """
        pass

    @property
    @abstractmethod
    def flag_types(self) -> list[FlagType]:
        """Flag types this detector can produce."""
        pass
