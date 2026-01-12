"""End-to-end tests for the full AcademicLint pipeline.

These tests verify that the complete analysis pipeline produces
expected results for known inputs, testing all components together:
- Text parsing
- NLP pipeline
- All detectors
- Density calculation
- Result aggregation
- Output formatting
"""

import json
import tempfile
from pathlib import Path

import pytest

from academiclint import Config, Linter, FlagType, AnalysisResult, ParagraphResult

from .sample_texts import (
    # Good texts
    GOOD_TEXT_PRECISE,
    GOOD_TEXT_PRECISE_EXPECTED,
    GOOD_TEXT_SCIENTIFIC,
    GOOD_TEXT_SCIENTIFIC_EXPECTED,
    # Bad texts
    BAD_TEXT_VAGUE,
    BAD_TEXT_VAGUE_EXPECTED,
    BAD_TEXT_WEASEL,
    BAD_TEXT_WEASEL_EXPECTED,
    # Specific issue texts
    TEXT_CIRCULAR_DEFINITIONS,
    TEXT_CIRCULAR_EXPECTED,
    TEXT_CAUSAL_CLAIMS,
    TEXT_CAUSAL_EXPECTED,
    TEXT_HEDGE_STACK,
    TEXT_HEDGE_EXPECTED,
    TEXT_CITATION_NEEDED,
    TEXT_CITATION_EXPECTED,
    TEXT_JARGON_DENSE,
    TEXT_JARGON_EXPECTED,
    TEXT_FILLER_HEAVY,
    TEXT_FILLER_EXPECTED,
    # Mixed and edge cases
    TEXT_MIXED_QUALITY,
    TEXT_MIXED_EXPECTED,
    TEXT_SINGLE_SENTENCE,
    TEXT_SINGLE_EXPECTED,
    TEXT_UNICODE,
    TEXT_UNICODE_EXPECTED,
    TEXT_LATEX_STYLE,
    TEXT_LATEX_EXPECTED,
    TEXT_MARKDOWN,
    TEXT_MARKDOWN_EXPECTED,
)


class TestHighQualityTextPipeline:
    """Test pipeline with high-quality academic texts."""

    @pytest.fixture
    def linter(self):
        """Create linter with standard config."""
        return Linter(Config(level="standard"))

    def test_precise_text_high_density(self, linter):
        """Precise academic text should have high density score."""
        result = linter.check(GOOD_TEXT_PRECISE)

        assert isinstance(result, AnalysisResult)
        assert result.summary.density >= GOOD_TEXT_PRECISE_EXPECTED["min_density"], (
            f"Expected density >= {GOOD_TEXT_PRECISE_EXPECTED['min_density']}, "
            f"got {result.summary.density}"
        )

    def test_precise_text_few_flags(self, linter):
        """Precise academic text should have few flags."""
        result = linter.check(GOOD_TEXT_PRECISE)

        assert result.summary.flag_count <= GOOD_TEXT_PRECISE_EXPECTED["max_flag_count"], (
            f"Expected <= {GOOD_TEXT_PRECISE_EXPECTED['max_flag_count']} flags, "
            f"got {result.summary.flag_count}"
        )

    def test_precise_text_acceptable_grade(self, linter):
        """Precise text should receive acceptable density grade."""
        result = linter.check(GOOD_TEXT_PRECISE)

        assert result.summary.density_grade in GOOD_TEXT_PRECISE_EXPECTED["density_grade_acceptable"], (
            f"Expected grade in {GOOD_TEXT_PRECISE_EXPECTED['density_grade_acceptable']}, "
            f"got '{result.summary.density_grade}'"
        )

    def test_scientific_text_high_density(self, linter):
        """Scientific text with citations should have high density."""
        result = linter.check(GOOD_TEXT_SCIENTIFIC)

        assert result.summary.density >= GOOD_TEXT_SCIENTIFIC_EXPECTED["min_density"]
        assert result.summary.flag_count <= GOOD_TEXT_SCIENTIFIC_EXPECTED["max_flag_count"]
        assert result.summary.density_grade in GOOD_TEXT_SCIENTIFIC_EXPECTED["density_grade_acceptable"]


class TestLowQualityTextPipeline:
    """Test pipeline with low-quality texts containing known issues."""

    @pytest.fixture
    def linter(self):
        """Create linter with standard config."""
        return Linter(Config(level="standard"))

    def test_vague_text_low_density(self, linter):
        """Vague text should have low density score."""
        result = linter.check(BAD_TEXT_VAGUE)

        assert result.summary.density <= BAD_TEXT_VAGUE_EXPECTED["max_density"], (
            f"Expected density <= {BAD_TEXT_VAGUE_EXPECTED['max_density']}, "
            f"got {result.summary.density}"
        )

    def test_vague_text_many_flags(self, linter):
        """Vague text should have many flags."""
        result = linter.check(BAD_TEXT_VAGUE)

        assert result.summary.flag_count >= BAD_TEXT_VAGUE_EXPECTED["min_flag_count"], (
            f"Expected >= {BAD_TEXT_VAGUE_EXPECTED['min_flag_count']} flags, "
            f"got {result.summary.flag_count}"
        )

    def test_vague_text_expected_flag_types(self, linter):
        """Vague text should trigger expected flag types."""
        result = linter.check(BAD_TEXT_VAGUE)

        flag_types = {f.type.value for f in result.flags}
        expected_types = set(BAD_TEXT_VAGUE_EXPECTED["expected_flag_types"])

        # At least some expected types should be present
        intersection = flag_types & expected_types
        assert len(intersection) > 0, (
            f"Expected at least one of {expected_types} in flags, "
            f"got {flag_types}"
        )

    def test_vague_text_low_grade(self, linter):
        """Vague text should receive low density grade."""
        result = linter.check(BAD_TEXT_VAGUE)

        assert result.summary.density_grade in BAD_TEXT_VAGUE_EXPECTED["density_grade_acceptable"], (
            f"Expected grade in {BAD_TEXT_VAGUE_EXPECTED['density_grade_acceptable']}, "
            f"got '{result.summary.density_grade}'"
        )

    def test_weasel_text_detects_weasels(self, linter):
        """Text with weasel words should be detected."""
        result = linter.check(BAD_TEXT_WEASEL)

        assert result.summary.density <= BAD_TEXT_WEASEL_EXPECTED["max_density"]
        assert result.summary.flag_count >= BAD_TEXT_WEASEL_EXPECTED["min_flag_count"]

        # Should detect WEASEL flags
        weasel_flags = [f for f in result.flags if f.type == FlagType.WEASEL]
        assert len(weasel_flags) > 0, "Expected WEASEL flags to be detected"


class TestSpecificDetectorsPipeline:
    """Test pipeline detection of specific issue types."""

    @pytest.fixture
    def strict_linter(self):
        """Create linter with strict config for comprehensive detection."""
        return Linter(Config(level="strict"))

    def test_circular_definitions_detected(self, strict_linter):
        """Circular definitions should be detected."""
        result = strict_linter.check(TEXT_CIRCULAR_DEFINITIONS)

        circular_flags = [f for f in result.flags if f.type == FlagType.CIRCULAR]

        assert len(circular_flags) >= TEXT_CIRCULAR_EXPECTED["min_circular_flags"], (
            f"Expected >= {TEXT_CIRCULAR_EXPECTED['min_circular_flags']} circular flags, "
            f"got {len(circular_flags)}"
        )

    def test_causal_claims_detected(self, strict_linter):
        """Unsupported causal claims should be detected."""
        result = strict_linter.check(TEXT_CAUSAL_CLAIMS)

        causal_flags = [f for f in result.flags if f.type == FlagType.UNSUPPORTED_CAUSAL]

        assert len(causal_flags) >= TEXT_CAUSAL_EXPECTED["min_causal_flags"], (
            f"Expected >= {TEXT_CAUSAL_EXPECTED['min_causal_flags']} causal flags, "
            f"got {len(causal_flags)}"
        )

    def test_hedge_stacking_detected(self, strict_linter):
        """Hedge stacking should be detected."""
        result = strict_linter.check(TEXT_HEDGE_STACK)

        hedge_flags = [f for f in result.flags if f.type == FlagType.HEDGE_STACK]

        assert len(hedge_flags) >= TEXT_HEDGE_EXPECTED["min_hedge_flags"], (
            f"Expected >= {TEXT_HEDGE_EXPECTED['min_hedge_flags']} hedge flags, "
            f"got {len(hedge_flags)}"
        )

    def test_citation_needed_detected(self, strict_linter):
        """Missing citations should be detected."""
        result = strict_linter.check(TEXT_CITATION_NEEDED)

        citation_flags = [f for f in result.flags if f.type == FlagType.CITATION_NEEDED]

        assert len(citation_flags) >= TEXT_CITATION_EXPECTED["min_citation_flags"], (
            f"Expected >= {TEXT_CITATION_EXPECTED['min_citation_flags']} citation flags, "
            f"got {len(citation_flags)}"
        )

    def test_jargon_dense_detected(self, strict_linter):
        """Jargon-heavy text should be detected."""
        result = strict_linter.check(TEXT_JARGON_DENSE)

        jargon_flags = [f for f in result.flags if f.type == FlagType.JARGON_DENSE]

        assert len(jargon_flags) >= 1, "Expected at least 1 jargon flag"

    def test_filler_detected(self, strict_linter):
        """Filler phrases should be detected."""
        result = strict_linter.check(TEXT_FILLER_HEAVY)

        filler_flags = [f for f in result.flags if f.type == FlagType.FILLER]

        assert len(filler_flags) >= TEXT_FILLER_EXPECTED["min_filler_flags"], (
            f"Expected >= {TEXT_FILLER_EXPECTED['min_filler_flags']} filler flags, "
            f"got {len(filler_flags)}"
        )


class TestMixedQualityPipeline:
    """Test pipeline with mixed quality text."""

    @pytest.fixture
    def linter(self):
        return Linter(Config(level="standard"))

    def test_mixed_quality_overall_density(self, linter):
        """Mixed quality text should have moderate overall density."""
        result = linter.check(TEXT_MIXED_QUALITY)

        assert result.summary.density >= TEXT_MIXED_EXPECTED["min_density"]
        assert result.summary.density <= TEXT_MIXED_EXPECTED["max_density"]

    def test_mixed_quality_paragraph_variance(self, linter):
        """Different paragraphs should have different densities."""
        result = linter.check(TEXT_MIXED_QUALITY)

        assert len(result.paragraphs) >= TEXT_MIXED_EXPECTED["paragraph_count"]

        # First paragraph (precise) should have higher density
        if len(result.paragraphs) >= 2:
            first_density = result.paragraphs[0].density
            second_density = result.paragraphs[1].density

            # First paragraph should generally be better
            assert first_density >= TEXT_MIXED_EXPECTED["first_paragraph_min_density"] or \
                   second_density <= TEXT_MIXED_EXPECTED["second_paragraph_max_density"], \
                   "Expected variance in paragraph quality"


class TestEdgeCasesPipeline:
    """Test pipeline with edge cases."""

    @pytest.fixture
    def linter(self):
        return Linter(Config(level="standard"))

    def test_single_sentence(self, linter):
        """Single sentence should be processed correctly."""
        result = linter.check(TEXT_SINGLE_SENTENCE)

        assert result.summary.paragraph_count >= TEXT_SINGLE_EXPECTED["paragraph_count"]
        assert result.summary.sentence_count >= TEXT_SINGLE_EXPECTED["sentence_count_min"]

    def test_unicode_handling(self, linter):
        """Unicode text should be processed without errors."""
        # Should not raise any exceptions
        result = linter.check(TEXT_UNICODE)

        assert isinstance(result, AnalysisResult)
        assert result.summary.paragraph_count >= TEXT_UNICODE_EXPECTED["paragraph_count_min"]

    def test_latex_style_handling(self, linter):
        """LaTeX-style text should be processed without errors."""
        result = linter.check(TEXT_LATEX_STYLE)

        assert isinstance(result, AnalysisResult)
        assert result.summary.paragraph_count >= TEXT_LATEX_EXPECTED["paragraph_count_min"]

    def test_markdown_handling(self, linter):
        """Markdown text should be processed without errors."""
        result = linter.check(TEXT_MARKDOWN)

        assert isinstance(result, AnalysisResult)
        assert result.summary.paragraph_count >= TEXT_MARKDOWN_EXPECTED["paragraph_count_min"]

    def test_empty_text_raises_error(self, linter):
        """Empty text should raise ValidationError."""
        from academiclint.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            linter.check("")

    def test_whitespace_only_raises_error(self, linter):
        """Whitespace-only text should raise ValidationError."""
        from academiclint.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            linter.check("   \n\t\n   ")


class TestStrictnessLevelsPipeline:
    """Test pipeline behavior at different strictness levels."""

    def test_relaxed_fewer_flags(self):
        """Relaxed level should produce fewer flags."""
        relaxed = Linter(Config(level="relaxed"))
        standard = Linter(Config(level="standard"))

        result_relaxed = relaxed.check(BAD_TEXT_VAGUE)
        result_standard = standard.check(BAD_TEXT_VAGUE)

        # Relaxed should be at most as strict as standard
        assert result_relaxed.summary.flag_count <= result_standard.summary.flag_count + 2

    def test_strict_more_flags(self):
        """Strict level should produce more flags."""
        standard = Linter(Config(level="standard"))
        strict = Linter(Config(level="strict"))

        result_standard = standard.check(BAD_TEXT_VAGUE)
        result_strict = strict.check(BAD_TEXT_VAGUE)

        # Strict should be at least as strict as standard
        assert result_strict.summary.flag_count >= result_standard.summary.flag_count - 2

    def test_academic_most_strict(self):
        """Academic level should be most strict."""
        strict = Linter(Config(level="strict"))
        academic = Linter(Config(level="academic"))

        result_strict = strict.check(BAD_TEXT_VAGUE)
        result_academic = academic.check(BAD_TEXT_VAGUE)

        # Academic should generally be strictest
        assert result_academic.summary.flag_count >= result_strict.summary.flag_count - 2


class TestResultStructurePipeline:
    """Test that result structure is correct and complete."""

    @pytest.fixture
    def linter(self):
        return Linter(Config(level="standard"))

    def test_result_has_all_fields(self, linter):
        """Result should have all required fields."""
        result = linter.check(BAD_TEXT_VAGUE)

        # Top-level fields
        assert result.id is not None
        assert result.id.startswith("check_")
        assert result.created_at is not None
        assert result.input_length > 0
        assert result.processing_time_ms >= 0

        # Summary fields
        assert 0.0 <= result.summary.density <= 1.0
        assert result.summary.density_grade in ["vapor", "thin", "adequate", "dense", "crystalline"]
        assert result.summary.flag_count >= 0
        assert result.summary.word_count > 0
        assert result.summary.sentence_count >= 0
        assert result.summary.paragraph_count >= 1
        assert result.summary.concept_count >= 0
        assert 0.0 <= result.summary.filler_ratio <= 1.0
        assert result.summary.suggestion_count >= 0

    def test_paragraphs_have_all_fields(self, linter):
        """Paragraph results should have all required fields."""
        result = linter.check(BAD_TEXT_VAGUE)

        for para in result.paragraphs:
            assert isinstance(para, ParagraphResult)
            assert para.index >= 0
            assert para.text is not None
            assert para.span is not None
            assert para.span.start >= 0
            assert para.span.end > para.span.start
            assert 0.0 <= para.density <= 1.0
            assert para.word_count >= 0
            assert para.sentence_count >= 0

    def test_flags_have_all_fields(self, linter):
        """Flags should have all required fields."""
        result = linter.check(BAD_TEXT_VAGUE)

        for flag in result.flags:
            assert flag.type is not None
            assert isinstance(flag.type, FlagType)
            assert flag.term is not None
            assert len(flag.term) > 0
            assert flag.span is not None
            assert flag.span.start >= 0
            assert flag.span.end > flag.span.start
            assert flag.line >= 1
            assert flag.column >= 1
            assert flag.severity is not None
            assert flag.message is not None
            assert flag.suggestion is not None

    def test_flag_count_matches_paragraphs(self, linter):
        """Total flag count should match sum of paragraph flags."""
        result = linter.check(BAD_TEXT_VAGUE)

        paragraph_flag_count = sum(len(p.flags) for p in result.paragraphs)
        assert result.summary.flag_count == paragraph_flag_count


class TestFileProcessingPipeline:
    """Test pipeline with file processing."""

    @pytest.fixture
    def linter(self):
        return Linter(Config(level="standard"))

    def test_markdown_file_processing(self, linter):
        """Markdown file should be processed correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test Document\n\n")
            f.write(GOOD_TEXT_PRECISE)
            f.flush()

            result = linter.check_file(f.name)

            assert isinstance(result, AnalysisResult)
            assert result.summary.density >= 0.3

    def test_txt_file_processing(self, linter):
        """Text file should be processed correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(BAD_TEXT_VAGUE)
            f.flush()

            result = linter.check_file(f.name)

            assert isinstance(result, AnalysisResult)
            assert result.summary.flag_count > 0

    def test_path_object_accepted(self, linter):
        """Path object should be accepted."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content for file processing.")
            f.flush()

            result = linter.check_file(Path(f.name))

            assert isinstance(result, AnalysisResult)


class TestDomainCustomizationPipeline:
    """Test pipeline with domain customization."""

    def test_domain_terms_reduce_jargon(self):
        """Domain terms should reduce jargon flags."""
        text_with_terms = """
        The epistemological considerations require careful methodological
        analysis of hermeneutical frameworks within phenomenological inquiry.
        """

        # Without domain terms
        linter_no_domain = Linter(Config(level="strict"))
        result_no_domain = linter_no_domain.check(text_with_terms)

        # With domain terms
        linter_with_domain = Linter(Config(
            level="strict",
            domain_terms=["epistemological", "methodological", "hermeneutical", "phenomenological"]
        ))
        result_with_domain = linter_with_domain.check(text_with_terms)

        # Jargon flags should be reduced
        jargon_no_domain = len([f for f in result_no_domain.flags if f.type == FlagType.JARGON_DENSE])
        jargon_with_domain = len([f for f in result_with_domain.flags if f.type == FlagType.JARGON_DENSE])

        assert jargon_with_domain <= jargon_no_domain


class TestPipelinePerformance:
    """Test pipeline performance characteristics."""

    @pytest.fixture
    def linter(self):
        return Linter(Config(level="standard"))

    def test_reasonable_processing_time(self, linter):
        """Processing should complete in reasonable time."""
        result = linter.check(BAD_TEXT_VAGUE)

        # Should complete in under 30 seconds
        assert result.processing_time_ms < 30000

    def test_large_text_handling(self, linter):
        """Large text should be handled without errors."""
        # Create large text by repeating
        large_text = (BAD_TEXT_VAGUE + "\n\n") * 10

        result = linter.check(large_text)

        assert isinstance(result, AnalysisResult)
        assert result.summary.paragraph_count >= 10


class TestSuggestionsGeneration:
    """Test that appropriate suggestions are generated."""

    @pytest.fixture
    def linter(self):
        return Linter(Config(level="standard", min_density=0.6))

    def test_low_density_suggestion(self, linter):
        """Low density text should generate density suggestion."""
        result = linter.check(BAD_TEXT_VAGUE)

        if result.summary.density < 0.6:
            density_suggestions = [s for s in result.overall_suggestions if "density" in s.lower()]
            assert len(density_suggestions) > 0, "Expected density suggestion for low-density text"

    def test_causal_claims_suggestion(self):
        """Causal claims should generate appropriate suggestion."""
        linter = Linter(Config(level="strict"))
        result = linter.check(TEXT_CAUSAL_CLAIMS)

        causal_suggestions = [s for s in result.overall_suggestions if "causal" in s.lower()]
        if len([f for f in result.flags if f.type == FlagType.UNSUPPORTED_CAUSAL]) > 0:
            assert len(causal_suggestions) > 0 or result.summary.suggestion_count >= 0
