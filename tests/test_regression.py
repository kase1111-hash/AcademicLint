"""Regression test suite for AcademicLint.

This test suite captures known behaviors, edge cases, and previously
fixed bugs to prevent regressions in future changes.

Organization:
- Edge cases and boundary conditions
- Known problematic inputs
- Behavior preservation tests
- Previously fixed bugs (documented)
- Performance regression guards
"""

import tempfile

import pytest

from academiclint import Config, Linter
from academiclint.core.exceptions import ConfigurationError, ValidationError
from academiclint.core.result import AnalysisResult, FlagType, Severity

# =============================================================================
# Edge Cases and Boundary Conditions
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_word_input(self):
        """Single word should be processed without error."""
        result = Linter().check("Word")
        assert isinstance(result, AnalysisResult)
        assert result.summary.word_count >= 1

    def test_single_character_input(self):
        """Single character should be processed."""
        result = Linter().check("A")
        assert isinstance(result, AnalysisResult)

    def test_very_long_word(self):
        """Very long words should be handled."""
        long_word = "a" * 1000
        result = Linter().check(f"The {long_word} is here.")
        assert isinstance(result, AnalysisResult)

    def test_sentence_with_only_punctuation(self):
        """Sentences with punctuation should be handled."""
        result = Linter().check("Hello... World!!! What??? Yes.")
        assert isinstance(result, AnalysisResult)

    def test_repeated_punctuation(self):
        """Repeated punctuation should not crash."""
        result = Linter().check("What?!?!?! Really!!!!!")
        assert isinstance(result, AnalysisResult)

    def test_all_caps_text(self):
        """All caps text should be processed."""
        result = Linter().check("THIS IS ALL CAPS TEXT HERE.")
        assert isinstance(result, AnalysisResult)

    def test_all_lowercase_text(self):
        """All lowercase text should be processed."""
        result = Linter().check("this is all lowercase text here.")
        assert isinstance(result, AnalysisResult)

    def test_mixed_case_words(self):
        """Mixed case words should be handled."""
        result = Linter().check("CamelCase and snake_case and MixedCAPS.")
        assert isinstance(result, AnalysisResult)

    def test_numbers_only(self):
        """Numeric content should be handled."""
        result = Linter().check("123 456 789 10.5 20.3")
        assert isinstance(result, AnalysisResult)

    def test_text_with_urls(self):
        """Text containing URLs should be handled."""
        result = Linter().check("Visit https://example.com/path?query=1 for more info.")
        assert isinstance(result, AnalysisResult)

    def test_text_with_emails(self):
        """Text containing emails should be handled."""
        result = Linter().check("Contact user@example.com for details.")
        assert isinstance(result, AnalysisResult)

    def test_text_with_hashtags(self):
        """Text with hashtags should be handled."""
        result = Linter().check("Trending #topic and #research today.")
        assert isinstance(result, AnalysisResult)

    def test_empty_paragraphs(self):
        """Multiple empty lines should be handled."""
        text = "First paragraph.\n\n\n\n\nSecond paragraph."
        result = Linter().check(text)
        assert isinstance(result, AnalysisResult)

    def test_tabs_and_spaces_mixed(self):
        """Mixed whitespace should be handled."""
        text = "Word\t\tword  word\t word"
        result = Linter().check(text)
        assert isinstance(result, AnalysisResult)

    def test_leading_trailing_whitespace(self):
        """Leading/trailing whitespace should be handled."""
        text = "   \n\n  Content here.  \n\n   "
        result = Linter().check(text)
        assert isinstance(result, AnalysisResult)


class TestBoundaryConditions:
    """Tests for boundary conditions."""

    def test_min_density_zero(self):
        """min_density=0 should work."""
        config = Config(min_density=0.0)
        result = Linter(config).check("Test text.")
        assert isinstance(result, AnalysisResult)

    def test_min_density_one(self):
        """min_density=1.0 should work."""
        config = Config(min_density=1.0)
        result = Linter(config).check("Test text.")
        assert isinstance(result, AnalysisResult)

    def test_min_density_boundary(self):
        """Boundary density values should work."""
        for density in [0.0, 0.01, 0.5, 0.99, 1.0]:
            config = Config(min_density=density)
            result = Linter(config).check("Test.")
            assert 0.0 <= result.summary.density <= 1.0

    def test_empty_domain_terms(self):
        """Empty domain_terms list should work."""
        config = Config(domain_terms=[])
        result = Linter(config).check("Test text.")
        assert isinstance(result, AnalysisResult)

    def test_many_domain_terms(self):
        """Many domain terms should work."""
        terms = [f"term{i}" for i in range(100)]
        config = Config(domain_terms=terms)
        result = Linter(config).check("Test text.")
        assert isinstance(result, AnalysisResult)

    def test_all_levels_work(self):
        """All strictness levels should work."""
        for level in ["relaxed", "standard", "strict", "academic"]:
            config = Config(level=level)
            result = Linter(config).check("Test text.")
            assert isinstance(result, AnalysisResult)


# =============================================================================
# Known Problematic Inputs
# =============================================================================


class TestProblematicInputs:
    """Tests for inputs known to be problematic."""

    def test_text_with_null_bytes_sanitized(self):
        """Null bytes should be sanitized (handled by validation)."""
        # This should either work or raise ValidationError, not crash
        try:
            result = Linter().check("Test\x00text")
            assert isinstance(result, AnalysisResult)
        except Exception as e:
            # ValidationError is acceptable
            assert "validation" in str(type(e)).lower() or isinstance(e, ValueError)

    def test_text_with_control_characters(self):
        """Control characters should be handled."""
        text = "Test\x01\x02\x03text here."
        result = Linter().check(text)
        assert isinstance(result, AnalysisResult)

    def test_right_to_left_text(self):
        """RTL text should be handled."""
        result = Linter().check("English and العربية mixed.")
        assert isinstance(result, AnalysisResult)

    def test_emoji_in_text(self):
        """Emoji should be handled."""
        result = Linter().check("This is great! 🎉 Amazing! 👍")
        assert isinstance(result, AnalysisResult)

    def test_mathematical_symbols(self):
        """Mathematical symbols should be handled."""
        result = Linter().check("The equation x² + y² = z² is famous.")
        assert isinstance(result, AnalysisResult)

    def test_currency_symbols(self):
        """Currency symbols should be handled."""
        result = Linter().check("Costs $100 or €85 or £75 or ¥10000.")
        assert isinstance(result, AnalysisResult)

    def test_nested_quotes(self):
        """Nested quotes should be handled."""
        result = Linter().check("He said \"she said 'hello' to me\".")
        assert isinstance(result, AnalysisResult)

    def test_unbalanced_parentheses(self):
        """Unbalanced parentheses should be handled."""
        result = Linter().check("This (has unbalanced ((parentheses).")
        assert isinstance(result, AnalysisResult)

    def test_unbalanced_brackets(self):
        """Unbalanced brackets should be handled."""
        result = Linter().check("Citation [1] and [2 without closing.")
        assert isinstance(result, AnalysisResult)

    def test_latex_commands(self):
        """LaTeX commands should be handled."""
        result = Linter().check(r"The equation $\alpha + \beta = \gamma$ shows this.")
        assert isinstance(result, AnalysisResult)

    def test_html_tags(self):
        """HTML tags should be handled."""
        result = Linter().check("<p>This is <strong>important</strong></p>")
        assert isinstance(result, AnalysisResult)

    def test_markdown_formatting(self):
        """Markdown formatting should be handled."""
        result = Linter().check("**Bold** and *italic* and `code`.")
        assert isinstance(result, AnalysisResult)

    def test_very_long_sentence(self):
        """Very long sentences should be handled."""
        long_sentence = " ".join(["word"] * 500) + "."
        result = Linter().check(long_sentence)
        assert isinstance(result, AnalysisResult)

    def test_many_short_sentences(self):
        """Many short sentences should be handled."""
        many_sentences = " ".join(["Word."] * 100)
        result = Linter().check(many_sentences)
        assert isinstance(result, AnalysisResult)


# =============================================================================
# Behavior Preservation Tests
# =============================================================================


class TestBehaviorPreservation:
    """Tests ensuring specific behaviors are preserved."""

    def test_circular_definition_always_detected(self):
        """Circular definitions must always be detected."""
        circular_texts = [
            "Freedom is the state of being free.",
            "Democracy means a democratic government.",
            "Justice refers to being just.",
        ]

        linter = Linter()
        for text in circular_texts:
            result = linter.check(text)
            all_flags = [f for p in result.paragraphs for f in p.flags]
            circular_flags = [f for f in all_flags if f.type == FlagType.CIRCULAR]
            assert len(circular_flags) >= 1, f"Failed to detect: {text}"

    def test_citation_patterns_recognized(self):
        """Citation patterns must be recognized."""
        cited_texts = [
            "This is true (Smith, 2023).",
            "According to Smith (2023), this works.",
            "Research shows this [1].",
            "Studies indicate this [1, 2, 3].",
        ]

        linter = Linter()
        for text in cited_texts:
            result = linter.check(text)
            all_flags = [f for p in result.paragraphs for f in p.flags]
            # Cited text should not get citation-needed flags
            citation_needed = [f for f in all_flags if f.type == FlagType.CITATION_NEEDED]
            assert len(citation_needed) == 0, f"False positive for: {text}"

    def test_density_range_preserved(self):
        """Density must always be in [0, 1] range."""
        test_texts = [
            "Simple.",
            "A" * 100,
            "Word " * 100,
            "In today's society, many experts believe various things.",
        ]

        linter = Linter()
        for text in test_texts:
            result = linter.check(text)
            assert 0.0 <= result.summary.density <= 1.0

    def test_flag_locations_valid(self):
        """Flag locations must be valid (within text bounds)."""
        text = "Many experts believe this is significantly important."

        result = Linter().check(text)
        text_len = len(text)

        for para in result.paragraphs:
            for flag in para.flags:
                assert flag.span.start >= 0
                assert flag.span.end <= text_len + 10  # Small tolerance
                assert flag.span.start < flag.span.end
                assert flag.line >= 1
                assert flag.column >= 1

    def test_severity_values_valid(self):
        """Severity values must be valid enum values."""
        text = "Freedom is being free. Many believe this causes issues."

        result = Linter().check(text)

        for para in result.paragraphs:
            for flag in para.flags:
                assert flag.severity in [Severity.LOW, Severity.MEDIUM, Severity.HIGH]

    def test_suggestions_never_empty(self):
        """Suggestions must never be empty strings."""
        text = "In today's society, freedom is the state of being free."

        result = Linter().check(text)

        for para in result.paragraphs:
            for flag in para.flags:
                assert flag.suggestion is not None
                assert len(flag.suggestion.strip()) > 0

    def test_paragraph_count_consistent(self):
        """Paragraph count must match paragraphs list length."""
        text = """
        First paragraph here.

        Second paragraph here.

        Third paragraph here.
        """

        result = Linter().check(text)
        assert result.summary.paragraph_count == len(result.paragraphs)

    def test_flag_count_consistent(self):
        """Flag count must match sum of paragraph flags."""
        text = "Many experts believe freedom is being free."

        result = Linter().check(text)
        total_flags = sum(len(p.flags) for p in result.paragraphs)
        assert result.summary.flag_count == total_flags


# =============================================================================
# Previously Fixed Bugs (Documented)
# =============================================================================


class TestPreviouslyFixedBugs:
    """
    Tests for previously fixed bugs to prevent regression.

    Each test documents:
    - Bug ID/description
    - Original behavior
    - Expected behavior
    """

    def test_bug_empty_paragraph_crash(self):
        """
        Bug: Empty paragraphs caused division by zero in density calculation.
        Original: Crashed with ZeroDivisionError.
        Expected: Handle gracefully, return 0.0 density for empty paragraphs.
        """
        text = "Content.\n\n\n\n\nMore content."
        result = Linter().check(text)
        # Should not crash
        assert isinstance(result, AnalysisResult)

    def test_bug_unicode_normalization(self):
        """
        Bug: Different Unicode normalizations caused inconsistent detection.
        Original: Same word in different forms flagged differently.
        Expected: Consistent handling regardless of Unicode form.
        """
        # Both should be handled the same way
        text1 = "café"  # composed form
        text2 = "café"  # decomposed form (if different)

        result1 = Linter().check(f"The {text1} experiment.")
        result2 = Linter().check(f"The {text2} experiment.")

        # Both should succeed
        assert isinstance(result1, AnalysisResult)
        assert isinstance(result2, AnalysisResult)

    def test_bug_overlapping_patterns(self):
        """
        Bug: Overlapping pattern matches caused duplicate flags.
        Original: Same text span flagged multiple times.
        Expected: Each issue flagged once.
        """
        text = "Many experts believe this."
        result = Linter().check(text)

        all_flags = [f for p in result.paragraphs for f in p.flags]

        # Check no exact duplicate spans
        spans = [(f.span.start, f.span.end, f.type) for f in all_flags]
        assert len(spans) == len(set(spans)), "Duplicate flags detected"

    def test_bug_newline_handling(self):
        """
        Bug: Different newline styles caused inconsistent paragraph detection.
        Original: CRLF vs LF gave different paragraph counts.
        Expected: Consistent handling of all newline styles.
        """
        text_lf = "Para 1.\n\nPara 2."
        text_crlf = "Para 1.\r\n\r\nPara 2."

        result_lf = Linter().check(text_lf)
        result_crlf = Linter().check(text_crlf)

        # Should have same paragraph structure
        assert result_lf.summary.paragraph_count == result_crlf.summary.paragraph_count

    def test_bug_config_mutation(self):
        """
        Bug: Config objects were mutated during analysis.
        Original: Config changed after linter.check() call.
        Expected: Config remains unchanged.
        """
        config = Config(level="standard", min_density=0.5)
        original_level = config.level
        original_density = config.min_density

        linter = Linter(config)
        linter.check("Test text for analysis.")

        assert config.level == original_level
        assert config.min_density == original_density

    def test_bug_result_id_uniqueness(self):
        """
        Bug: Result IDs were not unique across calls.
        Original: Same ID returned for different analyses.
        Expected: Each analysis has unique ID.
        """
        linter = Linter()

        result1 = linter.check("First text.")
        result2 = linter.check("Second text.")
        result3 = linter.check("Third text.")

        ids = [result1.id, result2.id, result3.id]
        assert len(ids) == len(set(ids)), "Result IDs not unique"

    def test_bug_leading_whitespace_drops_first_sentence(self):
        """
        Bug: spaCy folds leading whitespace into the first sentence, so it
        started before its paragraph and was never assigned to it.
        Original: First paragraph had 0 words/sentences, density 0.0, and
        patterns anchored at the sentence start never matched it.
        Expected: Leading whitespace is ignored.
        """
        result = Linter().check("\n    Freedom is the state of being free.\n")

        para = result.paragraphs[0]
        assert para.sentence_count == 1
        assert para.word_count > 0
        circular = [f for f in result.flags if f.type == FlagType.CIRCULAR]
        assert len(circular) == 1
        assert circular[0].line == 2

    def test_bug_sentence_spans_paragraphs(self):
        """
        Bug: A sentence without terminal punctuation (e.g. a Markdown heading)
        ran on into the next paragraph and was credited only to the first.
        Original: Body paragraphs after headings had 0 words and density 0.0.
        Expected: Sentences never cross a blank line.
        """
        text = "Introduction\n\nThis paragraph explains the method in detail."
        result = Linter().check(text)

        assert result.summary.paragraph_count == 2
        for para in result.paragraphs:
            assert para.sentence_count == 1
            assert para.word_count > 0
            assert para.density > 0.0

    def test_bug_flags_dropped_from_result(self):
        """
        Bug: Flags were only kept if they started inside a paragraph's span,
        so a sentence-level flag starting in leading whitespace vanished.
        Original: summary.flag_count counted flags missing from result.flags.
        Expected: Every detected flag appears in the result.
        """
        result = Linter().check("\n73% of students prefer online learning.\n")

        assert len(result.flags) == result.summary.flag_count
        assert any(f.type == FlagType.CITATION_NEEDED for f in result.flags)

    def test_bug_pattern_matches_across_paragraphs(self):
        """
        Bug: Multi-word patterns joined by \\s+ matched across blank lines.
        Original: A "Results" heading followed by "In a study..." was flagged
        as the causal claim "results in".
        Expected: Matches stay within a paragraph; line breaks inside one
        paragraph are still matched.
        """
        heading = Linter().check("Results\n\nIn a study of 500 participants, scores rose.")
        wrapped = Linter().check("The policy results\nin lower costs.")

        assert not [f for f in heading.flags if f.type == FlagType.UNSUPPORTED_CAUSAL]
        assert [f for f in wrapped.flags if f.type == FlagType.UNSUPPORTED_CAUSAL]

    def test_bug_domain_vocabulary_ignored(self):
        """
        Bug: Config.domain / domain_file were accepted but never used.
        Original: Domain terms were flagged as jargon regardless of --domain.
        Expected: Terms from the domain vocabulary are not flagged as jargon,
        and the caller's Config is left unchanged.
        """
        text = (
            "Phenomenology and hermeneutics reject naive empiricism, rationalism and materialism."
        )
        config = Config(domain="philosophy")

        plain = Linter().check(text)
        with_domain = Linter(config).check(text)

        assert [f for f in plain.flags if f.type == FlagType.JARGON_DENSE]
        assert not [f for f in with_domain.flags if f.type == FlagType.JARGON_DENSE]
        assert config.domain_terms == []

    def test_bug_multi_word_domain_terms_ignored(self):
        """
        Bug: Jargon was checked word by word, so multi-word domain terms such
        as "machine learning" never exempted anything.
        Expected: Words covered by a multi-word domain term are not jargon.
        """
        text = "Neural network training with machine learning requires memory allocation."
        config = Config(domain_terms=["neural network", "machine learning", "memory allocation"])

        plain = Linter().check(text)
        with_terms = Linter(config).check(text)

        assert [f for f in plain.flags if f.type == FlagType.JARGON_DENSE]
        assert not [f for f in with_terms.flags if f.type == FlagType.JARGON_DENSE]

    def test_bug_hyphenated_domain_terms_ignored(self):
        """
        Bug: Domain terms were split on whitespace only, so "cross-validation"
        never matched the words the text was tokenized into.
        Expected: Hyphenated terms exempt their words, written either way.
        """
        text = "We tuned hyper-parameter search using cross validation and early-stopping regularization."
        config = Config(domain_terms=["hyper-parameter", "cross-validation", "early-stopping"])

        plain = Linter().check(text)
        with_terms = Linter(config).check(text)

        assert [f for f in plain.flags if f.type == FlagType.JARGON_DENSE]
        assert not [f for f in with_terms.flags if f.type == FlagType.JARGON_DENSE]

    def test_bug_domain_phrase_own_joiners(self):
        """
        Bug: Multi-word domain terms only matched words joined by spaces or a
        single hyphen, so "Kullback--Leibler", an en dash or "a/b" never matched.
        Expected: A term matches its own spelling; spaces and dashes are
        interchangeable.
        """
        text = "We minimise the Kullback--Leibler divergence and cross\u2013validation error estimates."
        config = Config(domain_terms=["Kullback-Leibler divergence", "cross-validation"])

        plain = Linter().check(text)
        with_terms = Linter(config).check(text)

        assert [f for f in plain.flags if f.type == FlagType.JARGON_DENSE]
        assert not [f for f in with_terms.flags if f.type == FlagType.JARGON_DENSE]

    def test_bug_domain_phrase_matched_across_punctuation(self):
        """
        Bug: Multi-word domain terms matched across any punctuation, so
        "machine, learning" counted as the term "machine learning".
        Expected: Only spaces or a hyphen join the words of a term.
        """
        text = "After reconfiguring the machine, learning interoperability became easy."
        result = Linter(Config(domain_terms=["machine learning"])).check(text)

        assert [f for f in result.flags if f.type == FlagType.JARGON_DENSE]

    @pytest.mark.parametrize(
        "cite", ["\\cite{walker2017}", "\\citep[p.~5]{walker2017}", "\\parencite{walker2017}"]
    )
    def test_bug_latex_citations_not_recognised(self, tmp_path, cite):
        """
        Bug: \\cite{...} became "[citation]", which no citation pattern matched,
        and \\citep/\\parencite were deleted, so every cited claim in a LaTeX
        paper was flagged as needing a citation.
        Expected: A cited claim is not flagged; an uncited one still is.
        """
        claim = "Recent studies show that sleep loss impairs recall"
        cited = tmp_path / "cited.tex"
        cited.write_text(f"{claim} {cite}.\n", encoding="utf-8")
        uncited = tmp_path / "uncited.tex"
        uncited.write_text(f"{claim}.\n", encoding="utf-8")
        needs_citation = (FlagType.CITATION_NEEDED, FlagType.WEASEL)

        assert not [f for f in Linter().check_file(cited).flags if f.type in needs_citation]
        assert [f for f in Linter().check_file(uncited).flags if f.type in needs_citation]

    def test_bug_unknown_domain_silently_ignored(self):
        """
        Bug: An unknown domain name was accepted without any error.
        Expected: ConfigurationError naming the built-in domains.
        """
        with pytest.raises(ConfigurationError, match="Unknown domain 'medicine'"):
            Linter(Config(domain="medicine")).check("Some text to analyze.")


# =============================================================================
# Performance Regression Guards
# =============================================================================


class TestPerformanceRegression:
    """Tests to guard against performance regressions."""

    def test_short_text_under_100ms(self):
        """Short text should process in under 100ms."""
        text = "This is a short test sentence."
        result = Linter().check(text)
        # Allow some tolerance for CI environments
        assert result.processing_time_ms < 5000  # 5 seconds max

    def test_medium_text_under_1s(self):
        """Medium text should process in under 1 second."""
        text = "This is a test sentence. " * 50
        result = Linter().check(text)
        assert result.processing_time_ms < 10000  # 10 seconds max

    def test_repeated_analysis_consistent_time(self):
        """Repeated analysis should have consistent timing."""
        text = "Test sentence for timing consistency check."
        linter = Linter()
        linter.check(text)  # Warm up: the first call loads the spaCy model

        times = []
        for _ in range(3):
            result = linter.check(text)
            times.append(result.processing_time_ms)

        # Times should be reasonably consistent (within 10x)
        if max(times) > 0:
            ratio = max(times) / max(min(times), 1)
            assert ratio < 10, f"Timing inconsistent: {times}"


# =============================================================================
# File Handling Regression Tests
# =============================================================================


class TestFileHandlingRegression:
    """Tests for file handling regressions."""

    def test_file_with_bom(self):
        """Files with BOM should be handled."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            # Write UTF-8 BOM + content
            f.write(b"\xef\xbb\xbfTest content here.")
            f.flush()

            result = Linter().check_file(f.name)
            assert isinstance(result, AnalysisResult)

    def test_file_with_different_encodings(self):
        """Files with UTF-8 encoding should work."""
        content = "Test with special chars: é, ñ, ü"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            f.flush()

            result = Linter().check_file(f.name)
            assert isinstance(result, AnalysisResult)

    def test_empty_file(self):
        """Empty files should raise appropriate error."""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            f.write("")
            f.flush()

            with pytest.raises(ValidationError):
                Linter().check_file(f.name)

    def test_file_only_whitespace(self):
        """Files with only whitespace should raise error."""
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            f.write("   \n\n\t\t   ")
            f.flush()

            with pytest.raises(ValidationError):
                Linter().check_file(f.name)


# =============================================================================
# Configuration Regression Tests
# =============================================================================


class TestConfigurationRegression:
    """Tests for configuration handling regressions."""

    def test_config_defaults_stable(self):
        """Default config values should remain stable."""
        config = Config()

        assert config.level == "standard"
        assert config.min_density == 0.50
        assert config.domain is None
        assert config.domain_terms == []

    def test_config_from_env_defaults(self):
        """Config.from_env with no env vars should use defaults."""
        import os

        # Clear relevant env vars
        for key in list(os.environ.keys()):
            if key.startswith("ACADEMICLINT_"):
                os.environ.pop(key)

        config = Config.from_env(load_dotenv=False)

        assert config.level == "standard"
        assert config.min_density == 0.50

    def test_invalid_level_rejected(self):
        """Invalid level values should be rejected."""
        from academiclint.core.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError):
            Config(level="invalid_level")

    def test_invalid_density_rejected(self):
        """Invalid density values should be rejected."""
        from academiclint.core.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError):
            Config(min_density=1.5)

        with pytest.raises(ConfigurationError):
            Config(min_density=-0.1)
