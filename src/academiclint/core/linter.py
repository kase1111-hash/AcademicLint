"""Main Linter class for AcademicLint."""

import dataclasses
import logging
import time
import uuid
from bisect import bisect_right
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from academiclint.core.config import Config
from academiclint.core.exceptions import (
    AcademicLintError,
    ConfigurationError,
    ParsingError,
    ValidationError,
)
from academiclint.core.result import (
    AnalysisResult,
    Flag,
    ParagraphResult,
    Summary,
)
from academiclint.utils.validation import (
    validate_file_path,
    validate_paths,
    validate_text,
)

if TYPE_CHECKING:
    from academiclint.core.pipeline import NLPPipeline, ProcessedDocument
    from academiclint.detectors.base import Detector

logger = logging.getLogger(__name__)


class Linter:
    """Main entry point for text analysis.

    The Linter class provides methods to analyze text for semantic clarity
    issues including vagueness, unsupported causal claims, circular definitions,
    weasel words, and more.
    """

    def __init__(self, config: Config | None = None):
        """Initialize linter with configuration.

        Args:
            config: Linter configuration. Uses defaults if not provided.

        Raises:
            ValidationError: If the config is not a Config instance
            ConfigurationError: If the config values are invalid
        """
        if config is not None and not isinstance(config, Config):
            raise ValidationError(f"config must be a Config instance, got {type(config).__name__}")
        self.config = config or Config()
        self._nlp: NLPPipeline | None = None  # Lazy-loaded NLP pipeline
        self._detectors: list[Detector] | None = None  # Lazy-loaded detector modules

    def _ensure_pipeline(self) -> "NLPPipeline":
        """Ensure NLP pipeline is loaded.

        Returns:
            The NLP pipeline

        Raises:
            ModelNotFoundError: If spaCy model is not installed
            ModelLoadError: If spaCy or the model fails to load
        """
        if self._nlp is None:
            from academiclint.core.pipeline import NLPPipeline

            self._nlp = NLPPipeline()
        return self._nlp

    def _ensure_detectors(self) -> "list[Detector]":
        """Ensure detector modules are loaded.

        Returns:
            The detector instances
        """
        if self._detectors is None:
            from academiclint.detectors import get_all_detectors

            self._detectors = get_all_detectors()
        return self._detectors

    def check(self, text: str) -> AnalysisResult:
        """Analyze text for semantic clarity issues.

        Args:
            text: The text to analyze (Markdown, plain text, or LaTeX)

        Returns:
            AnalysisResult with all findings

        Raises:
            ValidationError: If the text is invalid (None, empty, or too long)
            ModelNotFoundError: If spaCy model is not installed
            ProcessingError: If NLP processing fails
            DetectorError: If a detector fails (only in strict mode)
        """
        # Validate and sanitize input
        text = validate_text(text)

        start_time = time.perf_counter()
        check_id = f"check_{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(UTC).isoformat()

        logger.info("Starting analysis [id=%s, length=%d chars]", check_id, len(text))
        logger.debug(
            "Configuration: level=%s, min_density=%.2f", self.config.level, self.config.min_density
        )

        detector_config = self._detector_config()
        nlp = self._ensure_pipeline()
        detectors = self._ensure_detectors()

        # Process document through NLP pipeline
        logger.debug("Processing document through NLP pipeline")
        doc = nlp.process(text)
        logger.debug(
            "NLP processing complete: %d tokens, %d sentences, %d paragraphs",
            len(doc.tokens),
            len(doc.sentences),
            len(doc.paragraphs),
        )

        # Run all detectors with error handling
        logger.debug("Running %d detectors", len(detectors))
        all_flags = []
        for detector in detectors:
            try:
                flags = detector.detect(doc, detector_config)
                all_flags.extend(flags)
            except AcademicLintError:
                # Re-raise our own exceptions
                raise
            except Exception as e:
                detector_name = type(detector).__name__
                logger.warning(
                    f"Detector {detector_name} failed: {e}",
                    exc_info=True,
                )
                # Continue with other detectors instead of failing completely
                # In strict mode, we could raise DetectorError here

        from academiclint.density import calculate_density

        paragraphs = self._build_paragraphs(doc, all_flags)
        total_words = sum(p.word_count for p in paragraphs)
        total_sentences = sum(p.sentence_count for p in paragraphs)

        # Calculate overall density using all document tokens
        try:
            all_tokens = [(token.text, token.lemma, token.is_stop) for token in doc.tokens]
            overall_density = calculate_density(
                text, all_flags, self.config, tokens_with_lemmas=all_tokens
            )
        except Exception as e:
            logger.warning(f"Failed to calculate overall density: {e}")
            overall_density = 0.0

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

        result = AnalysisResult(
            id=check_id,
            created_at=created_at,
            input_length=len(text),
            processing_time_ms=processing_time_ms,
            summary=summary,
            paragraphs=paragraphs,
            overall_suggestions=overall_suggestions,
        )

        logger.info(
            "Analysis complete [id=%s, time=%dms, flags=%d, density=%.2f (%s)]",
            check_id,
            processing_time_ms,
            len(all_flags),
            overall_density,
            density_grade,
        )

        return result

    def _build_paragraphs(
        self, doc: "ProcessedDocument", all_flags: list[Flag]
    ) -> list[ParagraphResult]:
        """Assign flags to paragraphs and score each paragraph's density."""
        from academiclint.density import calculate_density

        paragraphs = []

        # Assign each flag to the last paragraph starting at or before it, so a
        # flag that starts in leading whitespace or a paragraph gap is never
        # dropped from the result.
        para_starts = [para.span.start for para in doc.paragraphs]
        flags_by_para: list[list[Flag]] = [[] for _ in doc.paragraphs]
        if flags_by_para:
            for f in all_flags:
                index = max(bisect_right(para_starts, f.span.start) - 1, 0)
                flags_by_para[index].append(f)

        for i, para in enumerate(doc.paragraphs):
            try:
                para_flags = flags_by_para[i]
                # Extract tokens with lemmas from paragraph for accurate density calculation
                para_tokens = [
                    (token.text, token.lemma, token.is_stop)
                    for sent in para.sentences
                    for token in sent.tokens
                ]
                density = calculate_density(
                    para.text, para_flags, self.config, tokens_with_lemmas=para_tokens
                )

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
            except Exception as e:
                logger.warning(f"Failed to process paragraph {i}: {e}")
                # Create minimal paragraph result
                paragraphs.append(
                    ParagraphResult(
                        index=i,
                        text=para.text,
                        span=para.span,
                        density=0.0,
                        flags=flags_by_para[i],
                        word_count=para.word_count,
                        sentence_count=para.sentence_count,
                    )
                )

        return paragraphs

    def check_file(self, path: Path | str) -> AnalysisResult:
        """Analyze a file.

        Args:
            path: Path to file (supports .md, .txt, .tex)

        Returns:
            AnalysisResult with all findings

        Raises:
            ValidationError: If the path is invalid or file format unsupported
            FileNotFoundError: If the file doesn't exist
            ParsingError: If the file cannot be parsed
        """
        logger.info("Analyzing file: %s", path)

        # Validate file path
        validated_path = validate_file_path(path, must_exist=True, check_extension=True)
        logger.debug("File validated: %s", validated_path)

        from academiclint.core.parser import parse_document

        try:
            parsed = parse_document(validated_path)
            logger.debug("File parsed: %d characters", len(parsed.text))
        except Exception as e:
            logger.error("Failed to parse file %s: %s", path, e)
            if isinstance(e, (ValidationError, FileNotFoundError, ParsingError)):
                raise
            raise ParsingError(
                f"Failed to parse file: {e}",
                file_path=str(validated_path),
            ) from e

        result = self.check(parsed.text)

        # Report lines of the source file, not of the extracted text
        if parsed.source_lines is not None:
            for flag in result.flags:
                flag.line = parsed.source_line(flag.line)

        return result

    def check_files(self, paths: list[Path | str]) -> dict[Path, AnalysisResult]:
        """Analyze multiple files.

        Args:
            paths: List of file paths

        Returns:
            Dict mapping paths to results. Failed files will have error results.

        Raises:
            ValidationError: If the paths list is invalid
        """
        # Validate all paths first
        validated_paths = validate_paths(paths, must_exist=True, check_extension=True)

        results = {}
        for path in validated_paths:
            try:
                results[path] = self.check_file(path)
            except AcademicLintError as e:
                logger.error(f"Failed to analyze {path}: {e}")
                # Re-raise on first error; alternatively could collect errors
                raise

        return results

    def _detector_config(self) -> Config:
        """Return the config with the domain vocabulary merged into domain_terms.

        A copy is returned so the caller's Config is never mutated.

        Raises:
            ConfigurationError: If the domain or domain file cannot be loaded
        """
        config = self.config
        if config.domain is None and config.domain_file is None:
            return config

        from academiclint.domains.manager import DomainManager

        manager = DomainManager()
        terms = list(config.domain_terms)
        try:
            if config.domain is not None:
                is_builtin = config.domain in manager.BUILTIN_DOMAINS
                if not is_builtin and not Path(config.domain).is_file():
                    raise ConfigurationError(
                        f"Unknown domain '{config.domain}'. Built-in domains: "
                        f"{', '.join(sorted(manager.BUILTIN_DOMAINS))}"
                    )
                terms.extend(manager.get_terms(config.domain))
            if config.domain_file is not None:
                # Resolved, so a file named like a built-in domain is still read as a
                # file; get_terms also includes the terms of the file's `parent`
                terms.extend(manager.get_terms(str(Path(config.domain_file).resolve())))
        except (OSError, ValueError, yaml.YAMLError) as e:
            raise ConfigurationError(f"Failed to load domain vocabulary: {e}") from e

        return dataclasses.replace(config, domain_terms=terms)

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
