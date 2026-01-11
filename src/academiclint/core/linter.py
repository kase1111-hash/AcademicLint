"""Main Linter class for AcademicLint."""

import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from academiclint.core.config import Config
from academiclint.core.result import (
    AnalysisResult,
    ParagraphResult,
    Summary,
)


class Linter:
    """Main entry point for text analysis.

    The Linter class provides methods to analyze text for semantic clarity
    issues including vagueness, unsupported causal claims, circular definitions,
    weasel words, and more.
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize linter with configuration.

        Args:
            config: Linter configuration. Uses defaults if not provided.
        """
        self.config = config or Config()
        self._nlp = None  # Lazy-loaded NLP pipeline
        self._detectors = None  # Lazy-loaded detector modules

    def _ensure_pipeline(self) -> None:
        """Ensure NLP pipeline is loaded."""
        if self._nlp is None:
            from academiclint.core.pipeline import NLPPipeline

            self._nlp = NLPPipeline()

    def _ensure_detectors(self) -> None:
        """Ensure detector modules are loaded."""
        if self._detectors is None:
            from academiclint.detectors import get_all_detectors

            self._detectors = get_all_detectors()

    def check(self, text: str) -> AnalysisResult:
        """Analyze text for semantic clarity issues.

        Args:
            text: The text to analyze (Markdown, plain text, or LaTeX)

        Returns:
            AnalysisResult with all findings
        """
        start_time = time.perf_counter()
        check_id = f"check_{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).isoformat()

        self._ensure_pipeline()
        self._ensure_detectors()

        # Process document through NLP pipeline
        doc = self._nlp.process(text)

        # Run all detectors
        all_flags = []
        for detector in self._detectors:
            flags = detector.detect(doc, self.config)
            all_flags.extend(flags)

        # Calculate density for each paragraph
        from academiclint.density import calculate_density

        paragraphs = []
        total_words = 0
        total_sentences = 0

        for i, para in enumerate(doc.paragraphs):
            para_flags = [f for f in all_flags if para.span.start <= f.span.start < para.span.end]
            density = calculate_density(para.text, para_flags, self.config)

            para_result = ParagraphResult(
                index=i,
                text=para.text,
                span=para.span,
                density=density,
                flags=para_flags,
                word_count=para.word_count,
                sentence_count=para.sentence_count,
            )
            paragraphs.append(para_result)
            total_words += para.word_count
            total_sentences += para.sentence_count

        # Calculate overall density
        overall_density = calculate_density(text, all_flags, self.config)
        density_grade = self._get_density_grade(overall_density)

        # Generate overall suggestions
        overall_suggestions = self._generate_suggestions(all_flags, overall_density)

        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        summary = Summary(
            density=overall_density,
            density_grade=density_grade,
            flag_count=len(all_flags),
            word_count=total_words,
            sentence_count=total_sentences,
            paragraph_count=len(paragraphs),
            concept_count=doc.concept_count,
            filler_ratio=doc.filler_ratio,
            suggestion_count=len(overall_suggestions),
        )

        return AnalysisResult(
            id=check_id,
            created_at=created_at,
            input_length=len(text),
            processing_time_ms=processing_time_ms,
            summary=summary,
            paragraphs=paragraphs,
            overall_suggestions=overall_suggestions,
        )

    def check_file(self, path: Path) -> AnalysisResult:
        """Analyze a file.

        Args:
            path: Path to file (supports .md, .txt, .tex)

        Returns:
            AnalysisResult with all findings
        """
        from academiclint.core.parser import parse_file

        text = parse_file(path)
        return self.check(text)

    def check_files(self, paths: list[Path]) -> dict[Path, AnalysisResult]:
        """Analyze multiple files.

        Args:
            paths: List of file paths

        Returns:
            Dict mapping paths to results
        """
        results = {}
        for path in paths:
            results[path] = self.check_file(path)
        return results

    def check_stream(self, text: str) -> Iterator[ParagraphResult]:
        """Stream analysis paragraph by paragraph.

        For large documents, this allows processing without loading
        the entire result into memory.

        Args:
            text: The text to analyze

        Yields:
            ParagraphResult for each paragraph
        """
        result = self.check(text)
        yield from result.paragraphs

    def _get_density_grade(self, density: float) -> str:
        """Convert density score to grade label."""
        if density < 0.2:
            return "vapor"
        elif density < 0.4:
            return "thin"
        elif density < 0.6:
            return "adequate"
        elif density < 0.8:
            return "dense"
        else:
            return "crystalline"

    def _generate_suggestions(self, flags: list, density: float) -> list[str]:
        """Generate document-level suggestions based on analysis."""
        suggestions = []

        # Count flags by type
        from collections import Counter

        from academiclint.core.result import FlagType

        type_counts = Counter(f.type for f in flags)

        if type_counts.get(FlagType.HEDGE_STACK, 0) > 3:
            count = type_counts[FlagType.HEDGE_STACK]
            suggestions.append(f"Document relies heavily on hedged language ({count} instances)")

        if type_counts.get(FlagType.UNDERSPECIFIED, 0) > 5:
            suggestions.append("Consider specifying the scope in the introduction")

        causal_count = type_counts.get(FlagType.UNSUPPORTED_CAUSAL, 0)
        if causal_count > 0:
            suggestions.append(f"{causal_count} causal claim(s) lack cited evidence")

        if density < self.config.min_density:
            suggestions.append(
                f"Overall density ({density:.2f}) is below threshold ({self.config.min_density})"
            )

        return suggestions
