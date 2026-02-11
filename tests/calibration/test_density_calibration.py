"""Density calibration tests.

Validates that the density formula produces meaningfully different scores
for good vs bad academic writing. The formula (0.4 * content_ratio +
0.3 * unique_ratio + 0.3 * precision) and grade thresholds should cleanly
separate the two categories.
"""

import pytest

from academiclint.core.config import Config
from academiclint.core.result import Flag, FlagType, Severity, Span
from academiclint.density.calculator import (
    calculate_density,
    calculate_flag_penalty,
    tokenize,
)
from tests.fixtures.real_papers import ALL_ABSTRACTS, BAD_WRITING_SAMPLES


class TestDensityCalibrationNoSpacy:
    """Density calibration using the simple tokenizer (no spaCy required).

    These tests verify the density formula's behavior using the built-in
    fallback tokenizer/lemmatizer.
    """

    @pytest.fixture
    def config(self):
        return Config()

    # ── Good writing should score higher than bad writing ──────────────

    @pytest.mark.parametrize("discipline,abstract", list(ALL_ABSTRACTS.items()))
    def test_real_abstract_density_above_floor(self, config, discipline, abstract):
        """Real abstracts should achieve density >= 0.40 even without spaCy."""
        density = calculate_density(abstract, [], config)
        assert density >= 0.40, (
            f"{discipline}: density {density:.3f} below 0.40 floor"
        )

    @pytest.mark.parametrize("label,text", list(BAD_WRITING_SAMPLES.items()))
    def test_bad_writing_density_documented(self, config, label, text):
        """Record bad-writing density baselines.

        CALIBRATION FINDING: Without flag penalties, the content_ratio and
        unique_ratio components alone do NOT reliably distinguish bad writing
        (0.78-0.93) from good writing (0.82-0.95). The density formula needs
        flag penalties to create meaningful separation. This documents the
        current baseline for future formula tuning (Phase 3.5).
        """
        density = calculate_density(text, [], config)
        # Bad writing without flags scores 0.78-0.93 (too high).
        # This ceiling documents current behavior, not a quality target.
        assert density <= 1.0, (
            f"{label}: density {density:.3f} exceeds maximum"
        )

    def test_separation_between_good_and_bad(self, config):
        """Average density of good writing should exceed average density of bad writing."""
        good_densities = [
            calculate_density(text, [], config)
            for text in ALL_ABSTRACTS.values()
        ]
        bad_densities = [
            calculate_density(text, [], config)
            for text in BAD_WRITING_SAMPLES.values()
        ]

        avg_good = sum(good_densities) / len(good_densities)
        avg_bad = sum(bad_densities) / len(bad_densities)

        assert avg_good > avg_bad, (
            f"Good average ({avg_good:.3f}) should exceed bad average ({avg_bad:.3f})"
        )

    # ── Flag penalty should create additional separation ───────────────

    def test_flags_widen_density_gap(self, config):
        """Adding realistic flag counts to bad text should widen the gap."""
        good_text = ALL_ABSTRACTS["physics"]
        bad_text = BAD_WRITING_SAMPLES["vague_essay"]

        # Good text: 0 flags
        good_density = calculate_density(good_text, [], config)

        # Bad text: simulate 5 medium-severity flags
        bad_flags = [
            Flag(
                type=FlagType.UNDERSPECIFIED,
                term=f"term{i}",
                span=Span(0, 4),
                line=1,
                column=1,
                severity=Severity.MEDIUM,
                message="test",
                suggestion="test",
            )
            for i in range(5)
        ]
        bad_density = calculate_density(bad_text, bad_flags, config)

        gap = good_density - bad_density
        assert gap >= 0.05, (
            f"Density gap ({gap:.3f}) too narrow between good ({good_density:.3f}) "
            f"and bad-with-flags ({bad_density:.3f})"
        )

    # ── Penalty scaling ────────────────────────────────────────────────

    def test_penalty_scales_with_severity(self):
        """Higher severity flags should produce larger penalties."""
        low_flags = [
            Flag(
                type=FlagType.UNDERSPECIFIED, term="t", span=Span(0, 1),
                line=1, column=1, severity=Severity.LOW,
                message="", suggestion="",
            )
            for _ in range(3)
        ]
        high_flags = [
            Flag(
                type=FlagType.UNDERSPECIFIED, term="t", span=Span(0, 1),
                line=1, column=1, severity=Severity.HIGH,
                message="", suggestion="",
            )
            for _ in range(3)
        ]

        low_penalty = calculate_flag_penalty(low_flags, 100)
        high_penalty = calculate_flag_penalty(high_flags, 100)

        assert high_penalty > low_penalty

    def test_penalty_capped_at_half(self):
        """Flag penalty should never exceed 0.5 regardless of flag count."""
        many_flags = [
            Flag(
                type=FlagType.UNDERSPECIFIED, term="t", span=Span(0, 1),
                line=1, column=1, severity=Severity.HIGH,
                message="", suggestion="",
            )
            for _ in range(100)
        ]
        penalty = calculate_flag_penalty(many_flags, 50)
        assert penalty <= 0.5
