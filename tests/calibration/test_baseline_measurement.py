"""Baseline measurement of detector performance against real academic abstracts.

Runs every detector against 10 real abstracts and records flag counts.
This serves as a regression baseline: future detector improvements should
reduce false positives on these texts without losing true positives.
"""

import pytest

spacy = pytest.importorskip("spacy", reason="spaCy required for baseline measurement")

from academiclint import Config, Linter
from academiclint.core.result import FlagType
from tests.fixtures.real_papers import ALL_ABSTRACTS, BAD_WRITING_SAMPLES


@pytest.fixture(scope="module")
def linter():
    return Linter(Config(level="standard"))


class TestBaselineRealAbstracts:
    """Measure detector performance on real academic writing.

    Well-written abstracts with citations should produce few flags.
    These thresholds serve as a regression ceiling -- improvements to
    detectors should only push flag counts DOWN.
    """

    @pytest.mark.parametrize("discipline,abstract", list(ALL_ABSTRACTS.items()))
    def test_real_abstract_flag_count_bounded(self, linter, discipline, abstract):
        """Real abstracts should not produce excessive flags."""
        result = linter.check(abstract)
        # A well-cited, well-written abstract should produce at most 8 flags.
        # This ceiling will tighten as detectors become context-aware.
        assert result.summary.flag_count <= 8, (
            f"{discipline}: {result.summary.flag_count} flags is excessive. "
            f"Flags: {[(f.type.value, f.term) for f in result.flags]}"
        )

    @pytest.mark.parametrize("discipline,abstract", list(ALL_ABSTRACTS.items()))
    def test_real_abstract_density_above_floor(self, linter, discipline, abstract):
        """Real abstracts should achieve reasonable density scores."""
        result = linter.check(abstract)
        # Published academic writing should score at least 0.35 density.
        assert result.summary.density >= 0.35, (
            f"{discipline}: density {result.summary.density:.2f} is below floor. "
            f"Grade: {result.summary.density_grade}"
        )

    @pytest.mark.parametrize("discipline,abstract", list(ALL_ABSTRACTS.items()))
    def test_citations_suppress_weasel_flags(self, linter, discipline, abstract):
        """Abstracts with citations should not get citation-needed flags for cited claims."""
        result = linter.check(abstract)
        citation_flags = [f for f in result.flags if f.type == FlagType.CITATION_NEEDED]
        # Cited abstracts should have at most 2 citation flags (for uncited claims)
        assert len(citation_flags) <= 2, (
            f"{discipline}: {len(citation_flags)} citation flags despite citations present. "
            f"Terms: {[f.term for f in citation_flags]}"
        )


class TestBaselineBadWriting:
    """Verify detectors DO fire on intentionally bad writing.

    These are true-positive baselines -- detector improvements must
    not regress below these minimums.
    """

    def test_vague_essay_flagged(self, linter):
        """Vague essay should produce multiple vagueness flags."""
        result = linter.check(BAD_WRITING_SAMPLES["vague_essay"])
        vague_flags = [
            f for f in result.flags
            if f.type in (FlagType.UNDERSPECIFIED, FlagType.FILLER)
        ]
        assert len(vague_flags) >= 3, (
            f"Only {len(vague_flags)} vagueness/filler flags on intentionally vague text"
        )

    def test_circular_definitions_flagged(self, linter):
        """Circular definitions should be caught."""
        result = linter.check(BAD_WRITING_SAMPLES["circular_definitions"])
        circular_flags = [f for f in result.flags if f.type == FlagType.CIRCULAR_DEFINITION]
        assert len(circular_flags) >= 2, (
            f"Only {len(circular_flags)} circular flags on 4 circular definitions"
        )

    def test_unsupported_claims_flagged(self, linter):
        """Unsupported causal claims should be caught."""
        result = linter.check(BAD_WRITING_SAMPLES["unsupported_claims"])
        causal_flags = [f for f in result.flags if f.type == FlagType.UNSUPPORTED_CAUSAL]
        assert len(causal_flags) >= 2, (
            f"Only {len(causal_flags)} causal flags on 4 unsupported causal claims"
        )

    def test_filler_laden_flagged(self, linter):
        """Filler-laden text should produce filler flags."""
        result = linter.check(BAD_WRITING_SAMPLES["filler_laden"])
        filler_flags = [f for f in result.flags if f.type == FlagType.FILLER]
        assert len(filler_flags) >= 3, (
            f"Only {len(filler_flags)} filler flags on text packed with filler phrases"
        )

    def test_bad_writing_lower_density_than_good(self, linter):
        """Bad writing should consistently score lower density than good writing."""
        bad_density = linter.check(BAD_WRITING_SAMPLES["vague_essay"]).summary.density
        good_density = linter.check(ALL_ABSTRACTS["physics"]).summary.density

        assert bad_density < good_density, (
            f"Bad writing density ({bad_density:.2f}) should be lower than "
            f"good writing density ({good_density:.2f})"
        )
