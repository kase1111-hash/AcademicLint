"""Detector modules for AcademicLint."""

from academiclint.detectors.base import Detector
from academiclint.detectors.causal import CausalDetector
from academiclint.detectors.circular import CircularDetector
from academiclint.detectors.citation import CitationDetector
from academiclint.detectors.filler import FillerDetector
from academiclint.detectors.hedge import HedgeDetector
from academiclint.detectors.jargon import JargonDetector
from academiclint.detectors.vagueness import VaguenessDetector
from academiclint.detectors.weasel import WeaselDetector

__all__ = [
    "Detector",
    "VaguenessDetector",
    "CausalDetector",
    "CircularDetector",
    "WeaselDetector",
    "HedgeDetector",
    "JargonDetector",
    "CitationDetector",
    "FillerDetector",
    "get_all_detectors",
]


def get_all_detectors() -> list[Detector]:
    """Get all available detector instances.

    Returns:
        List of detector instances
    """
    return [
        VaguenessDetector(),
        CausalDetector(),
        CircularDetector(),
        WeaselDetector(),
        HedgeDetector(),
        JargonDetector(),
        CitationDetector(),
        FillerDetector(),
    ]
