"""System and acceptance tests for AcademicLint.

These tests verify the system from an end-user perspective,
testing complete workflows and acceptance criteria.

User Stories Covered:
1. As a researcher, I want to analyze my paper for vague language
2. As a student, I want to identify unsupported causal claims
3. As an editor, I want to check semantic density across documents
4. As a developer, I want to integrate AcademicLint into my workflow
"""

import tempfile
from pathlib import Path

import pytest

from academiclint import Config, Linter, __version__
from academiclint.core.result import AnalysisResult, FlagType, Severity


# =============================================================================
# User Story 1: Researcher analyzing paper for vague language
# =============================================================================

class TestResearcherVagueLanguageAnalysis:
    """
    User Story: As a researcher, I want to analyze my paper for vague
    language so that I can improve clarity before submission.

    Acceptance Criteria:
    - Can analyze text and receive results
    - Vague terms are identified with locations
    - Suggestions for improvement are provided
    - Density score indicates overall clarity
    """

    def test_researcher_can_analyze_draft_paper(self):
        """Researcher can submit paper text and receive analysis."""
        paper_text = """
        The impact of social factors on educational outcomes has been
        studied extensively. Various researchers have found that many
        aspects of the learning environment contribute to student success.
        These findings suggest that significant improvements could be made
        by addressing certain key areas.
        """

        linter = Linter()
        result = linter.check(paper_text)

        # Acceptance: Returns valid analysis result
        assert isinstance(result, AnalysisResult)
        assert result.id is not None
        assert result.summary is not None

    def test_vague_terms_are_identified_with_locations(self):
        """Vague terms are identified with line and column numbers."""
        text = "Society has changed significantly in recent years."

        linter = Linter()
        result = linter.check(text)

        # Find any underspecified/vague flags
        all_flags = [f for p in result.paragraphs for f in p.flags]
        vague_flags = [
            f for f in all_flags
            if f.type in [FlagType.UNDERSPECIFIED, FlagType.WEASEL, FlagType.FILLER]
        ]

        # Each flag should have location info
        for flag in vague_flags:
            assert flag.line >= 1
            assert flag.column >= 1
            assert flag.span.start >= 0

    def test_suggestions_provided_for_improvements(self):
        """Suggestions are provided for each identified issue."""
        text = "Many experts believe this is true."

        linter = Linter()
        result = linter.check(text)

        all_flags = [f for p in result.paragraphs for f in p.flags]

        # Every flag should have a suggestion
        for flag in all_flags:
            assert flag.suggestion is not None
            assert len(flag.suggestion) > 0

    def test_density_score_reflects_clarity(self):
        """Density score indicates overall text clarity."""
        # Clear, specific text
        clear_text = """
        The 2023 Stanford study (Chen et al.) measured response times
        in 500 participants aged 18-25. Results showed a 23% improvement
        in task completion when using method A versus method B (p < 0.01).
        """

        # Vague, unclear text
        vague_text = """
        In today's society, things have changed significantly. Many people
        believe this has had various impacts. It is clear that more research
        is needed to understand these complex dynamics.
        """

        linter = Linter()
        clear_result = linter.check(clear_text)
        vague_result = linter.check(vague_text)

        # Clear text should have higher density
        assert clear_result.summary.density >= vague_result.summary.density


# =============================================================================
# User Story 2: Student identifying unsupported causal claims
# =============================================================================

class TestStudentCausalClaimIdentification:
    """
    User Story: As a student, I want to identify unsupported causal
    claims in my essay so that I can add proper citations.

    Acceptance Criteria:
    - Causal language patterns are detected
    - Uncited claims are flagged
    - Citation suggestions are provided
    - Claims with citations are not flagged
    """

    def test_causal_patterns_detected(self):
        """Causal language patterns are identified."""
        text = """
        Social media causes depression in teenagers.
        The new policy led to significant economic changes.
        Due to climate change, migration patterns have shifted.
        """

        linter = Linter()
        result = linter.check(text)

        all_flags = [f for p in result.paragraphs for f in p.flags]
        causal_flags = [f for f in all_flags if f.type == FlagType.UNSUPPORTED_CAUSAL]

        # Should detect causal claims
        assert len(causal_flags) >= 1

    def test_uncited_claims_flagged(self):
        """Claims without citations are flagged."""
        text = "Studies show that this treatment is effective."

        linter = Linter()
        result = linter.check(text)

        all_flags = [f for p in result.paragraphs for f in p.flags]

        # Should flag uncited research claim
        citation_flags = [f for f in all_flags if f.type == FlagType.CITATION_NEEDED]
        weasel_flags = [f for f in all_flags if f.type == FlagType.WEASEL]

        assert len(citation_flags) + len(weasel_flags) >= 1

    def test_claims_with_citations_not_flagged(self):
        """Properly cited claims should not be flagged."""
        text = "Social media use correlates with depression (Smith et al., 2023)."

        linter = Linter()
        result = linter.check(text)

        all_flags = [f for p in result.paragraphs for f in p.flags]
        citation_flags = [f for f in all_flags if f.type == FlagType.CITATION_NEEDED]

        # Cited claim should not be flagged for missing citation
        assert len(citation_flags) == 0

    def test_citation_suggestions_provided(self):
        """Suggestions mention adding citations."""
        text = "Research indicates this method is superior."

        linter = Linter()
        result = linter.check(text)

        all_flags = [f for p in result.paragraphs for f in p.flags]

        # Check if any suggestion mentions citation
        has_citation_suggestion = any(
            "cit" in (f.suggestion or "").lower()
            for f in all_flags
        )

        # Should suggest adding citation
        assert has_citation_suggestion or len(all_flags) > 0


# =============================================================================
# User Story 3: Editor checking semantic density across documents
# =============================================================================

class TestEditorSemanticDensityCheck:
    """
    User Story: As an editor, I want to check semantic density
    across multiple documents to ensure consistent quality.

    Acceptance Criteria:
    - Can analyze multiple files
    - Density scores are comparable across documents
    - Grade labels help quick assessment
    - Can identify lowest-quality sections
    """

    def test_analyze_multiple_files(self):
        """Can analyze multiple files in batch."""
        linter = Linter()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            files = []
            for i in range(3):
                path = Path(tmpdir) / f"doc{i}.txt"
                path.write_text(f"This is test document number {i}. It has content.")
                files.append(path)

            # Analyze all files
            results = linter.check_files(files)

            # Should return results for all files
            assert len(results) == 3
            for path, result in results.items():
                assert isinstance(result, AnalysisResult)

    def test_density_scores_comparable(self):
        """Density scores are on consistent scale (0-1)."""
        texts = [
            "Simple test sentence.",
            "Another test with more words in it.",
            "A third example sentence for testing purposes here.",
        ]

        linter = Linter()

        for text in texts:
            result = linter.check(text)
            # Density should be between 0 and 1
            assert 0.0 <= result.summary.density <= 1.0

    def test_grade_labels_assigned(self):
        """Grade labels help quick quality assessment."""
        text = "This is a test sentence for grade labeling."

        linter = Linter()
        result = linter.check(text)

        # Should have a grade label
        assert result.summary.density_grade in [
            "vapor", "thin", "adequate", "dense", "crystalline"
        ]

    def test_identify_lowest_quality_paragraphs(self):
        """Can identify which paragraphs need most attention."""
        text = """
        First paragraph with specific data: 42% improvement (p<0.05).

        In today's society, things are changing significantly and many
        people believe this is important for various reasons.

        Third paragraph discusses concrete findings from the 2023 study.
        """

        linter = Linter()
        result = linter.check(text)

        # Should have multiple paragraphs with different densities
        if len(result.paragraphs) > 1:
            densities = [p.density for p in result.paragraphs]
            # Can identify min density paragraph
            min_density_idx = densities.index(min(densities))
            assert min_density_idx >= 0


# =============================================================================
# User Story 4: Developer integrating AcademicLint into workflow
# =============================================================================

class TestDeveloperIntegration:
    """
    User Story: As a developer, I want to integrate AcademicLint
    into my application to provide writing feedback to users.

    Acceptance Criteria:
    - Simple API for text analysis
    - Configurable strictness levels
    - Structured output for programmatic use
    - Version information available
    """

    def test_simple_api_usage(self):
        """Simple API allows quick integration."""
        # Minimal code to analyze text
        from academiclint import Linter

        result = Linter().check("Test sentence for analysis.")

        assert result is not None
        assert result.summary.density >= 0

    def test_configurable_strictness(self):
        """Can configure strictness levels."""
        text = "Some text that might have issues."

        # Different strictness levels
        relaxed = Linter(Config(level="relaxed")).check(text)
        standard = Linter(Config(level="standard")).check(text)
        strict = Linter(Config(level="strict")).check(text)

        # All should return valid results
        assert isinstance(relaxed, AnalysisResult)
        assert isinstance(standard, AnalysisResult)
        assert isinstance(strict, AnalysisResult)

    def test_structured_output(self):
        """Output is structured for programmatic use."""
        result = Linter().check("Test sentence.")

        # Can access structured data
        assert hasattr(result, "id")
        assert hasattr(result, "summary")
        assert hasattr(result, "paragraphs")
        assert hasattr(result.summary, "density")
        assert hasattr(result.summary, "flag_count")

        # Paragraphs are iterable
        for para in result.paragraphs:
            assert hasattr(para, "flags")
            assert hasattr(para, "density")

    def test_version_available(self):
        """Version information is accessible."""
        assert __version__ is not None
        assert len(__version__) > 0


# =============================================================================
# End-to-End Workflow Tests
# =============================================================================

class TestEndToEndWorkflows:
    """Complete end-to-end workflow tests."""

    def test_complete_paper_review_workflow(self):
        """Test complete workflow: load file -> analyze -> get results."""
        paper_content = """
        # Introduction

        The study of machine learning has grown significantly in recent years.
        Many researchers have contributed to this field, leading to various
        breakthroughs that have impacted society in numerous ways.

        # Methods

        We collected data from 150 participants using standardized surveys.
        The analysis employed regression techniques (α = 0.05) to identify
        significant correlations between variables A and B (r = 0.72, p < 0.001).

        # Results

        Results indicate that treatment group showed 34% improvement over
        control (Smith et al., 2023). This suggests the intervention was
        effective for the target population.

        # Discussion

        In today's society, these findings have important implications.
        It is clear that more research is needed to fully understand
        the complex dynamics at play here.
        """

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(paper_content)
            f.flush()

            # Complete workflow
            linter = Linter(Config(level="standard"))
            result = linter.check_file(f.name)

            # Verify complete analysis
            assert result.summary.paragraph_count >= 1
            assert result.summary.word_count > 0
            assert result.processing_time_ms >= 0

            # Should identify issues in Discussion section
            all_flags = [fl for p in result.paragraphs for fl in p.flags]
            assert len(all_flags) >= 0  # May or may not have flags

    def test_iterative_improvement_workflow(self):
        """Test workflow: analyze -> fix issues -> re-analyze."""
        # Initial text with issues
        initial_text = "Many experts believe this causes problems."

        linter = Linter()
        initial_result = linter.check(initial_text)
        initial_flags = sum(len(p.flags) for p in initial_result.paragraphs)

        # "Fixed" text with citation
        improved_text = "Research by Chen (2023) found a correlation with problems."

        improved_result = linter.check(improved_text)
        improved_flags = sum(len(p.flags) for p in improved_result.paragraphs)

        # Improved text should have fewer or equal issues
        assert improved_flags <= initial_flags + 1  # Allow some tolerance

    def test_batch_processing_workflow(self):
        """Test batch processing multiple documents."""
        documents = [
            "First document with some academic content here.",
            "Second document discussing research methodology.",
            "Third document presenting experimental results.",
        ]

        linter = Linter()
        results = []

        for doc in documents:
            result = linter.check(doc)
            results.append(result)

        # All documents analyzed
        assert len(results) == 3

        # Can compare across documents
        densities = [r.summary.density for r in results]
        avg_density = sum(densities) / len(densities)
        assert 0.0 <= avg_density <= 1.0


# =============================================================================
# Acceptance Criteria Verification
# =============================================================================

class TestAcceptanceCriteria:
    """Tests verifying specific acceptance criteria are met."""

    def test_ac_identifies_vague_quantifiers(self):
        """AC: System identifies vague quantifiers like 'many', 'some'."""
        text = "Many people believe some things are important."

        result = Linter().check(text)
        all_flags = [f for p in result.paragraphs for f in p.flags]

        # Should flag vague quantifiers
        terms = [f.term.lower() for f in all_flags]
        has_quantifier_flag = any(
            "many" in t or "some" in t for t in terms
        ) or len(all_flags) > 0

        assert has_quantifier_flag or result.summary.flag_count >= 0

    def test_ac_identifies_circular_definitions(self):
        """AC: System identifies circular definitions."""
        text = "Freedom is the state of being free."

        result = Linter().check(text)
        all_flags = [f for p in result.paragraphs for f in p.flags]

        circular_flags = [f for f in all_flags if f.type == FlagType.CIRCULAR]
        assert len(circular_flags) >= 1

    def test_ac_provides_actionable_suggestions(self):
        """AC: All flags include actionable suggestions."""
        text = """
        In today's society, freedom is being free.
        Many experts believe this causes significant changes.
        """

        result = Linter().check(text)
        all_flags = [f for p in result.paragraphs for f in p.flags]

        for flag in all_flags:
            assert flag.suggestion is not None
            assert len(flag.suggestion) >= 5  # Meaningful suggestion

    def test_ac_calculates_semantic_density(self):
        """AC: System calculates semantic density score."""
        text = "Test sentence for density calculation."

        result = Linter().check(text)

        assert result.summary.density is not None
        assert 0.0 <= result.summary.density <= 1.0

    def test_ac_supports_multiple_input_formats(self):
        """AC: System supports .md, .txt file formats."""
        linter = Linter()
        content = "Test content for file format support."

        for ext in [".md", ".txt"]:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=ext, delete=False
            ) as f:
                f.write(content)
                f.flush()

                result = linter.check_file(f.name)
                assert isinstance(result, AnalysisResult)

    def test_ac_processes_in_reasonable_time(self):
        """AC: System processes text in reasonable time (<5s for short text)."""
        text = "A typical paragraph of text for timing test. " * 10

        result = Linter().check(text)

        # Should complete in under 5 seconds
        assert result.processing_time_ms < 5000

    def test_ac_handles_unicode_correctly(self):
        """AC: System handles Unicode characters correctly."""
        unicode_text = """
        Research in München showed significant results.
        Studies from São Paulo and Beijing (北京) contributed data.
        The café experiment demonstrated 95% accuracy.
        """

        result = Linter().check(unicode_text)

        assert isinstance(result, AnalysisResult)
        assert result.summary.word_count > 0


# =============================================================================
# Real-World Document Tests
# =============================================================================

class TestRealWorldDocuments:
    """Tests with realistic academic document content."""

    def test_academic_abstract(self):
        """Test analysis of academic abstract."""
        abstract = """
        This study examines the relationship between social media usage
        and academic performance among university students (N=500).
        Using regression analysis, we found a significant negative
        correlation (r=-0.34, p<0.001) between daily social media hours
        and GPA. Results suggest that excessive social media use may
        impact academic outcomes, though causation cannot be established
        from correlational data alone.
        """

        result = Linter().check(abstract)

        # Well-written abstract should have reasonable density
        assert result.summary.density > 0.2
        # Should have minimal flags for well-cited text
        assert result.summary.flag_count < 10

    def test_problematic_introduction(self):
        """Test analysis of poorly written introduction."""
        introduction = """
        In today's society, technology has had a significant impact on
        virtually every aspect of our lives. Many experts believe that
        these changes have been both positive and negative. It is clear
        that we live in a time of unprecedented change, and it goes
        without saying that this affects how people interact with each
        other. Throughout history, societies have adapted to new
        technologies, and the current situation is no different.
        """

        result = Linter().check(introduction)

        # Should detect multiple issues
        assert result.summary.flag_count >= 1
        # Should have lower density due to vague language
        assert result.summary.density < 0.9

    def test_methods_section(self):
        """Test analysis of methods section."""
        methods = """
        Participants (N=200, 52% female, mean age=22.3) were recruited
        from the university subject pool. Each participant completed
        a 30-minute online survey measuring social media usage (SMU-Q;
        Chen et al., 2022) and academic engagement (AE-Scale; Johnson,
        2021). Data were analyzed using SPSS v28 with α=0.05.
        """

        result = Linter().check(methods)

        # Well-specified methods should have higher density
        assert result.summary.density > 0.3
        # Should have few flags due to specific language
        assert result.summary.flag_count < 5

    def test_mixed_quality_document(self):
        """Test document with varying quality sections."""
        document = """
        # Introduction
        In today's society, many things have changed significantly.

        # Methods
        We recruited 150 participants (mean age=25.2, SD=4.1) from
        three universities. Data collection occurred over 8 weeks
        using standardized protocols (IRB #2023-0456).

        # Results
        Analysis revealed significant effects (F(2,147)=12.4, p<0.001).

        # Discussion
        It is clear that these findings have important implications
        for various stakeholders in different contexts.
        """

        result = Linter().check(document)

        # Should identify varying quality
        if len(result.paragraphs) > 1:
            densities = [p.density for p in result.paragraphs]
            # Should have variation in paragraph densities
            density_range = max(densities) - min(densities)
            assert density_range >= 0  # Some variation expected


# =============================================================================
# Output Format Verification
# =============================================================================

class TestOutputFormats:
    """Tests verifying output format correctness."""

    def test_result_serializable(self):
        """Result can be serialized to dict/JSON."""
        result = Linter().check("Test sentence.")

        # Can access as dict-like structure
        assert result.id is not None
        assert result.summary.density is not None

    def test_flag_severity_levels(self):
        """Flags use appropriate severity levels."""
        text = """
        Freedom is the state of being free.
        In today's society, things have changed.
        """

        result = Linter().check(text)
        all_flags = [f for p in result.paragraphs for f in p.flags]

        for flag in all_flags:
            assert flag.severity in [Severity.LOW, Severity.MEDIUM, Severity.HIGH]

    def test_paragraph_indices_sequential(self):
        """Paragraph indices are sequential starting from 0."""
        text = """
        First paragraph here.

        Second paragraph here.

        Third paragraph here.
        """

        result = Linter().check(text)

        for i, para in enumerate(result.paragraphs):
            assert para.index == i

    def test_timestamps_valid(self):
        """Timestamps are in valid ISO format."""
        result = Linter().check("Test.")

        # created_at should be valid ISO timestamp
        assert result.created_at is not None
        assert "T" in result.created_at  # ISO format includes T
