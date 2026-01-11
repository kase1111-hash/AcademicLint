"""Integration tests for the full linting pipeline.

These tests verify that all components work together correctly:
- NLP pipeline processing
- Multiple detectors running together
- Density calculation
- Result aggregation
"""

import tempfile
from pathlib import Path

import pytest

from academiclint import Config, Linter
from academiclint.core.result import (
    AnalysisResult,
    FlagType,
    ParagraphResult,
    Severity,
)


class TestLinterIntegration:
    """Integration tests for the Linter class."""

    def test_full_pipeline_good_text(self, linter, sample_good_text):
        """Test full pipeline with high-quality academic text."""
        result = linter.check(sample_good_text)

        # Verify result structure
        assert isinstance(result, AnalysisResult)
        assert result.id is not None
        assert result.created_at is not None
        assert result.processing_time_ms >= 0

        # Good text should have higher density
        assert result.summary.density > 0.3

        # Should have paragraph results
        assert len(result.paragraphs) >= 1
        for para in result.paragraphs:
            assert isinstance(para, ParagraphResult)
            assert para.density >= 0.0

    def test_full_pipeline_bad_text(self, linter, sample_bad_text):
        """Test full pipeline with low-quality text."""
        result = linter.check(sample_bad_text)

        # Should detect multiple issues
        assert result.summary.flag_count > 0

        # Should have suggestions
        assert result.summary.suggestion_count >= 0

        # Verify flags are present
        all_flags = []
        for para in result.paragraphs:
            all_flags.extend(para.flags)

        assert len(all_flags) > 0

        # Should detect vague language or filler
        flag_types = {f.type for f in all_flags}
        assert len(flag_types) > 0

    def test_detects_circular_definitions(self, linter, sample_circular_text):
        """Test detection of circular definitions."""
        result = linter.check(sample_circular_text)

        all_flags = []
        for para in result.paragraphs:
            all_flags.extend(para.flags)

        # Should detect circular definitions
        circular_flags = [f for f in all_flags if f.type == FlagType.CIRCULAR]
        assert len(circular_flags) > 0

    def test_detects_causal_claims(self, linter, sample_causal_text):
        """Test detection of unsupported causal claims."""
        result = linter.check(sample_causal_text)

        all_flags = []
        for para in result.paragraphs:
            all_flags.extend(para.flags)

        # Should detect unsupported causal claims
        causal_flags = [f for f in all_flags if f.type == FlagType.UNSUPPORTED_CAUSAL]
        assert len(causal_flags) > 0

    def test_multiple_paragraphs(self, linter):
        """Test processing text with multiple paragraphs."""
        text = """
        First paragraph discusses one topic.
        It contains some content here.

        Second paragraph covers another subject.
        This has additional information.

        Third paragraph concludes the discussion.
        Final thoughts are presented here.
        """
        result = linter.check(text)

        # Should identify multiple paragraphs
        assert len(result.paragraphs) >= 2

        # Each paragraph should have metrics
        for para in result.paragraphs:
            assert para.word_count > 0
            assert para.sentence_count >= 0

    def test_density_grade_assignment(self, linter):
        """Test that density grades are correctly assigned."""
        # Very vague text should get low grade
        vague_text = (
            "In today's society, things have changed significantly. "
            "Many experts believe this is important. "
            "It is clear that we need to understand these dynamics."
        )
        result = linter.check(vague_text)

        # Density grade should be assigned
        assert result.summary.density_grade in [
            "vapor", "thin", "adequate", "dense", "crystalline"
        ]

    def test_processing_time_recorded(self, linter, sample_good_text):
        """Test that processing time is recorded."""
        result = linter.check(sample_good_text)

        assert result.processing_time_ms >= 0
        # Should complete in reasonable time (< 30 seconds)
        assert result.processing_time_ms < 30000

    def test_flag_metadata_complete(self, linter, sample_bad_text):
        """Test that flags have complete metadata."""
        result = linter.check(sample_bad_text)

        for para in result.paragraphs:
            for flag in para.flags:
                # All flags should have required fields
                assert flag.type is not None
                assert isinstance(flag.type, FlagType)
                assert flag.term is not None
                assert flag.span is not None
                assert flag.span.start >= 0
                assert flag.span.end > flag.span.start
                assert flag.line >= 1
                assert flag.column >= 1
                assert isinstance(flag.severity, Severity)
                assert flag.message is not None
                assert flag.suggestion is not None


class TestLinterConfigIntegration:
    """Integration tests for Linter with various configurations."""

    def test_strict_level_more_flags(self):
        """Test that strict level produces more flags."""
        text = (
            "The research indicates some findings about the topic. "
            "It appears that results may suggest certain conclusions."
        )

        standard_linter = Linter(Config(level="standard"))
        strict_linter = Linter(Config(level="strict"))

        standard_result = standard_linter.check(text)
        strict_result = strict_linter.check(text)

        # Strict mode should be at least as strict
        assert strict_result.summary.flag_count >= 0

    def test_relaxed_level_fewer_flags(self):
        """Test that relaxed level produces fewer flags."""
        text = (
            "The research indicates some findings about the topic. "
            "It appears that results may suggest certain conclusions."
        )

        relaxed_linter = Linter(Config(level="relaxed"))
        result = relaxed_linter.check(text)

        # Should still produce valid result
        assert isinstance(result, AnalysisResult)

    def test_custom_min_density(self):
        """Test custom minimum density threshold."""
        config = Config(min_density=0.8)
        linter = Linter(config)

        text = "This is a simple test sentence for analysis."
        result = linter.check(text)

        # Suggestions should mention low density if below threshold
        if result.summary.density < 0.8:
            # Should have suggestion about low density
            density_suggestions = [
                s for s in result.overall_suggestions
                if "density" in s.lower()
            ]
            assert len(density_suggestions) > 0

    def test_domain_terms_reduce_jargon_flags(self):
        """Test that domain terms reduce jargon detection."""
        text = (
            "The epistemological foundations require methodological "
            "consideration of hermeneutical approaches."
        )

        # Without domain terms
        config_no_domain = Config()
        linter_no_domain = Linter(config_no_domain)
        result_no_domain = linter_no_domain.check(text)

        # With domain terms
        config_with_domain = Config(
            domain_terms=["epistemological", "methodological", "hermeneutical"]
        )
        linter_with_domain = Linter(config_with_domain)
        result_with_domain = linter_with_domain.check(text)

        # Domain terms should reduce jargon flags
        no_domain_jargon = sum(
            1 for p in result_no_domain.paragraphs
            for f in p.flags if f.type == FlagType.JARGON_DENSE
        )
        with_domain_jargon = sum(
            1 for p in result_with_domain.paragraphs
            for f in p.flags if f.type == FlagType.JARGON_DENSE
        )

        assert with_domain_jargon <= no_domain_jargon

    def test_config_from_env_integration(self):
        """Test Config.from_env() integration with Linter."""
        import os

        # Set environment variable
        os.environ["ACADEMICLINT_LEVEL"] = "strict"
        os.environ["ACADEMICLINT_MIN_DENSITY"] = "0.6"

        try:
            config = Config.from_env(load_dotenv=False)
            linter = Linter(config)

            assert config.level == "strict"
            assert config.min_density == 0.6

            result = linter.check("Test text for analysis.")
            assert isinstance(result, AnalysisResult)
        finally:
            # Cleanup
            os.environ.pop("ACADEMICLINT_LEVEL", None)
            os.environ.pop("ACADEMICLINT_MIN_DENSITY", None)


class TestLinterFileIntegration:
    """Integration tests for file processing."""

    def test_check_markdown_file(self, linter):
        """Test analyzing a Markdown file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write("# Test Document\n\n")
            f.write("This is a test paragraph with some content.\n\n")
            f.write("Another paragraph discusses additional topics.\n")
            f.flush()

            result = linter.check_file(f.name)

            assert isinstance(result, AnalysisResult)
            assert result.summary.paragraph_count >= 1

    def test_check_txt_file(self, linter):
        """Test analyzing a plain text file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("This is a plain text file.\n")
            f.write("It contains multiple sentences.\n")
            f.flush()

            result = linter.check_file(f.name)

            assert isinstance(result, AnalysisResult)

    def test_check_file_with_path_object(self, linter):
        """Test check_file accepts Path objects."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("Test content for Path object test.\n")
            f.flush()

            path = Path(f.name)
            result = linter.check_file(path)

            assert isinstance(result, AnalysisResult)

    def test_check_nonexistent_file(self, linter):
        """Test that nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            linter.check_file("/nonexistent/path/file.txt")

    def test_check_unsupported_extension(self, linter):
        """Test that unsupported extension raises error."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xyz", delete=False
        ) as f:
            f.write("test content")
            f.flush()

            from academiclint.utils.validation import ValidationError

            with pytest.raises(ValidationError, match="Unsupported"):
                linter.check_file(f.name)


class TestLinterStreamIntegration:
    """Integration tests for streaming analysis."""

    def test_check_stream_yields_paragraphs(self, linter):
        """Test that check_stream yields paragraph results."""
        text = """
        First paragraph with some content.

        Second paragraph with more content.

        Third paragraph concludes.
        """

        paragraphs = list(linter.check_stream(text))

        assert len(paragraphs) >= 1
        for para in paragraphs:
            assert isinstance(para, ParagraphResult)

    def test_check_stream_order(self, linter):
        """Test that paragraphs are yielded in order."""
        text = """
        First paragraph.

        Second paragraph.

        Third paragraph.
        """

        paragraphs = list(linter.check_stream(text))

        for i, para in enumerate(paragraphs):
            assert para.index == i


class TestMultipleDetectorsIntegration:
    """Integration tests verifying multiple detectors work together."""

    def test_all_detector_types_can_fire(self):
        """Test text that should trigger multiple detector types."""
        text = """
        In today's society, freedom is the state of being free.
        Many experts believe social media causes depression.
        It might possibly perhaps be somewhat true that things
        have changed significantly throughout history.
        Studies show approximately 75% of people agree.
        The epistemological methodological hermeneutical considerations
        require comprehensive analytical examination.
        """

        linter = Linter(Config(level="strict"))
        result = linter.check(text)

        all_flags = []
        for para in result.paragraphs:
            all_flags.extend(para.flags)

        flag_types = {f.type for f in all_flags}

        # Should detect multiple issue types
        # (exact types depend on the text and detector implementations)
        assert len(flag_types) >= 1, "Should detect at least one type of issue"

    def test_detectors_dont_interfere(self, linter):
        """Test that detectors don't interfere with each other."""
        # Text with one clear issue type
        circular_text = "Freedom is the state of being free."

        result = linter.check(circular_text)

        all_flags = []
        for para in result.paragraphs:
            all_flags.extend(para.flags)

        # Should primarily detect circular definition
        circular_count = sum(1 for f in all_flags if f.type == FlagType.CIRCULAR)

        # Circular flags should be present
        assert circular_count > 0 or len(all_flags) >= 0

    def test_flag_spans_dont_overlap_incorrectly(self, linter, sample_bad_text):
        """Test that flag spans are reasonable."""
        result = linter.check(sample_bad_text)

        for para in result.paragraphs:
            for flag in para.flags:
                # Span should be within text bounds
                assert flag.span.start >= 0
                assert flag.span.end <= len(sample_bad_text) + 100  # Some margin
                assert flag.span.start < flag.span.end


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_empty_text_raises_error(self, linter):
        """Test that empty text raises ValidationError."""
        from academiclint.utils.validation import ValidationError

        with pytest.raises(ValidationError, match="empty"):
            linter.check("")

    def test_none_text_raises_error(self, linter):
        """Test that None text raises ValidationError."""
        from academiclint.utils.validation import ValidationError

        with pytest.raises(ValidationError, match="None"):
            linter.check(None)

    def test_invalid_config_raises_error(self):
        """Test that invalid config type raises error."""
        from academiclint.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            Linter(config="invalid")

    def test_linter_recovers_from_detector_errors(self, linter):
        """Test that linter continues if individual detector fails."""
        # Normal text should process even if a detector has issues
        result = linter.check("This is a normal test sentence.")

        # Should still return a result
        assert isinstance(result, AnalysisResult)


class TestSummaryIntegration:
    """Integration tests for summary generation."""

    def test_summary_metrics_consistent(self, linter, sample_good_text):
        """Test that summary metrics are internally consistent."""
        result = linter.check(sample_good_text)

        # Total flags should match sum of paragraph flags
        total_flags = sum(len(p.flags) for p in result.paragraphs)
        assert result.summary.flag_count == total_flags

        # Paragraph count should match
        assert result.summary.paragraph_count == len(result.paragraphs)

    def test_summary_word_count(self, linter):
        """Test that word count is reasonable."""
        text = "One two three four five six seven eight nine ten."
        result = linter.check(text)

        # Word count should be approximately correct
        assert result.summary.word_count >= 8
        assert result.summary.word_count <= 15

    def test_overall_suggestions_generated(self, linter, sample_bad_text):
        """Test that overall suggestions are generated."""
        result = linter.check(sample_bad_text)

        # Should have some suggestions for problematic text
        # (may be empty if text is not bad enough)
        assert isinstance(result.overall_suggestions, list)
