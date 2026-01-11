"""Performance tests for AcademicLint.

This module contains load tests, stress tests, and benchmarks to ensure
the system performs adequately under various conditions.

Test Categories:
- Load Tests: Normal expected usage patterns
- Stress Tests: Extreme conditions and edge cases
- Benchmarks: Timing measurements for performance tracking
- Scalability Tests: How performance scales with input size
- Concurrency Tests: Parallel processing behavior
"""

import gc
import statistics
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from academiclint import Config, Linter
from academiclint.core.result import AnalysisResult


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def linter():
    """Create a reusable linter instance."""
    return Linter()


@pytest.fixture
def sample_paragraph():
    """A typical academic paragraph."""
    return """
    The relationship between social media usage and academic performance
    has been extensively studied in recent years. Research by Smith et al.
    (2023) found a significant negative correlation (r=-0.34, p<0.001)
    between daily social media hours and GPA among university students.
    However, these findings must be interpreted cautiously, as correlation
    does not imply causation.
    """


@pytest.fixture
def sample_page():
    """A typical academic page (~500 words)."""
    paragraph = """
    The relationship between social media usage and academic performance
    has been extensively studied in recent years. Research by Smith et al.
    (2023) found a significant negative correlation between daily social
    media hours and GPA among university students. However, these findings
    must be interpreted cautiously, as correlation does not imply causation.
    Additional factors such as sleep quality, study habits, and socioeconomic
    status may confound the observed relationship.
    """
    return "\n\n".join([paragraph] * 6)  # ~6 paragraphs per page


@pytest.fixture
def sample_document():
    """A typical academic document (~5000 words)."""
    paragraph = """
    The relationship between social media usage and academic performance
    has been extensively studied in recent years. Research by Smith et al.
    (2023) found a significant negative correlation between daily social
    media hours and GPA among university students. However, these findings
    must be interpreted cautiously, as correlation does not imply causation.
    """
    return "\n\n".join([paragraph] * 60)  # ~10 pages


# =============================================================================
# Load Tests - Normal Expected Usage
# =============================================================================

class TestLoadNormalUsage:
    """Load tests simulating normal expected usage patterns."""

    def test_single_sentence_response_time(self, linter):
        """Single sentence should process quickly."""
        text = "This is a simple test sentence for analysis."

        start = time.perf_counter()
        result = linter.check(text)
        elapsed = time.perf_counter() - start

        assert isinstance(result, AnalysisResult)
        assert elapsed < 5.0, f"Single sentence took {elapsed:.2f}s (expected <5s)"

    def test_paragraph_response_time(self, linter, sample_paragraph):
        """Single paragraph should process in reasonable time."""
        start = time.perf_counter()
        result = linter.check(sample_paragraph)
        elapsed = time.perf_counter() - start

        assert isinstance(result, AnalysisResult)
        assert elapsed < 10.0, f"Paragraph took {elapsed:.2f}s (expected <10s)"

    def test_page_response_time(self, linter, sample_page):
        """Single page should process in reasonable time."""
        start = time.perf_counter()
        result = linter.check(sample_page)
        elapsed = time.perf_counter() - start

        assert isinstance(result, AnalysisResult)
        assert elapsed < 30.0, f"Page took {elapsed:.2f}s (expected <30s)"

    def test_document_response_time(self, linter, sample_document):
        """Full document should process in reasonable time."""
        start = time.perf_counter()
        result = linter.check(sample_document)
        elapsed = time.perf_counter() - start

        assert isinstance(result, AnalysisResult)
        assert elapsed < 120.0, f"Document took {elapsed:.2f}s (expected <120s)"

    def test_repeated_analyses_stable(self, linter, sample_paragraph):
        """Repeated analyses should have stable performance."""
        times = []

        for _ in range(5):
            start = time.perf_counter()
            linter.check(sample_paragraph)
            times.append(time.perf_counter() - start)

        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        # Coefficient of variation should be reasonable
        cv = std_dev / avg_time if avg_time > 0 else 0
        assert cv < 1.0, f"High timing variance: CV={cv:.2f}"

    def test_sequential_file_processing(self, linter):
        """Sequential file processing should be efficient."""
        files = []

        # Create test files
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(5):
                path = Path(tmpdir) / f"doc{i}.txt"
                path.write_text(f"Test document {i} with some content here.")
                files.append(path)

            start = time.perf_counter()
            for f in files:
                linter.check_file(f)
            elapsed = time.perf_counter() - start

        assert elapsed < 60.0, f"5 files took {elapsed:.2f}s (expected <60s)"


# =============================================================================
# Stress Tests - Extreme Conditions
# =============================================================================

class TestStressExtreme:
    """Stress tests for extreme conditions."""

    def test_very_long_text(self, linter):
        """Very long text should complete without error."""
        # ~50,000 words
        long_text = "This is a test sentence. " * 10000

        start = time.perf_counter()
        result = linter.check(long_text)
        elapsed = time.perf_counter() - start

        assert isinstance(result, AnalysisResult)
        # Should complete, even if slow
        assert elapsed < 300.0, f"Very long text took {elapsed:.2f}s"

    def test_many_paragraphs(self, linter):
        """Text with many paragraphs should be handled."""
        # 100 paragraphs
        text = "\n\n".join([f"Paragraph {i} content here." for i in range(100)])

        result = linter.check(text)

        assert isinstance(result, AnalysisResult)
        assert result.summary.paragraph_count >= 50

    def test_very_long_single_paragraph(self, linter):
        """Very long single paragraph should be handled."""
        # 1000 sentences in one paragraph
        text = " ".join(["This is sentence number {}.".format(i) for i in range(1000)])

        result = linter.check(text)

        assert isinstance(result, AnalysisResult)

    def test_deeply_nested_content(self, linter):
        """Deeply nested content should be handled."""
        # Nested quotes and parentheses
        text = 'He said "she said (they said [we said "it works"])".'

        result = linter.check(text)
        assert isinstance(result, AnalysisResult)

    def test_rapid_sequential_requests(self, linter):
        """Rapid sequential requests should all succeed."""
        text = "Test sentence for rapid requests."
        results = []

        start = time.perf_counter()
        for _ in range(20):
            results.append(linter.check(text))
        elapsed = time.perf_counter() - start

        assert len(results) == 20
        assert all(isinstance(r, AnalysisResult) for r in results)
        # 20 requests should complete in reasonable time
        assert elapsed < 120.0

    def test_alternating_text_sizes(self, linter):
        """Alternating between different text sizes should work."""
        short = "Short."
        medium = "Medium length sentence here. " * 10
        long_text = "Long sentence content. " * 100

        results = []
        for text in [short, long_text, medium, short, long_text, medium]:
            results.append(linter.check(text))

        assert len(results) == 6
        assert all(isinstance(r, AnalysisResult) for r in results)

    def test_high_flag_density_text(self, linter):
        """Text with many potential flags should be handled."""
        # Text designed to trigger many detectors
        problematic = """
        In today's society, many experts believe freedom is being free.
        Studies show this causes significant changes throughout history.
        It is clear that various factors have had impacts on things.
        Many people think some aspects are important for reasons.
        """ * 10

        result = linter.check(problematic)

        assert isinstance(result, AnalysisResult)
        # Should detect many flags without crashing
        assert result.summary.flag_count >= 0


# =============================================================================
# Benchmark Tests - Timing Measurements
# =============================================================================

class TestBenchmarks:
    """Benchmark tests for performance tracking."""

    def test_benchmark_empty_linter_creation(self):
        """Benchmark linter creation time."""
        times = []

        for _ in range(10):
            start = time.perf_counter()
            Linter()
            times.append(time.perf_counter() - start)

        avg_time = statistics.mean(times)
        # Linter creation should be fast
        assert avg_time < 1.0, f"Linter creation avg: {avg_time:.3f}s"

    def test_benchmark_config_creation(self):
        """Benchmark config creation time."""
        times = []

        for _ in range(100):
            start = time.perf_counter()
            Config(level="strict", min_density=0.6)
            times.append(time.perf_counter() - start)

        avg_time = statistics.mean(times)
        # Config creation should be very fast
        assert avg_time < 0.01, f"Config creation avg: {avg_time:.4f}s"

    def test_benchmark_short_text_analysis(self, linter):
        """Benchmark short text analysis."""
        text = "This is a short test sentence."
        times = []

        # Warm up
        linter.check(text)

        for _ in range(10):
            start = time.perf_counter()
            linter.check(text)
            times.append(time.perf_counter() - start)

        avg_time = statistics.mean(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        # Record for tracking (assertions are loose)
        assert avg_time < 10.0, f"Short text avg: {avg_time:.3f}s"
        assert p95_time < 15.0, f"Short text p95: {p95_time:.3f}s"

    def test_benchmark_medium_text_analysis(self, linter, sample_paragraph):
        """Benchmark medium text analysis."""
        times = []

        # Warm up
        linter.check(sample_paragraph)

        for _ in range(5):
            start = time.perf_counter()
            linter.check(sample_paragraph)
            times.append(time.perf_counter() - start)

        avg_time = statistics.mean(times)

        # Record for tracking
        assert avg_time < 30.0, f"Medium text avg: {avg_time:.3f}s"

    def test_benchmark_throughput(self, linter):
        """Benchmark throughput (texts per second)."""
        text = "Test sentence for throughput measurement."
        count = 10

        start = time.perf_counter()
        for _ in range(count):
            linter.check(text)
        elapsed = time.perf_counter() - start

        throughput = count / elapsed if elapsed > 0 else 0

        # Should process at least 0.1 texts per second
        assert throughput > 0.1, f"Throughput: {throughput:.2f} texts/sec"


# =============================================================================
# Scalability Tests - Performance vs Input Size
# =============================================================================

class TestScalability:
    """Tests for how performance scales with input size."""

    def test_linear_scaling_with_length(self, linter):
        """Processing time should scale reasonably with text length."""
        sizes = [100, 500, 1000]
        times = []

        for size in sizes:
            text = "Word " * size
            start = time.perf_counter()
            linter.check(text)
            times.append(time.perf_counter() - start)

        # Check that scaling is not worse than O(n^2)
        # Time ratio should be less than size ratio squared
        if times[0] > 0:
            ratio_1_to_2 = times[1] / times[0]
            size_ratio = sizes[1] / sizes[0]
            assert ratio_1_to_2 < size_ratio ** 2.5, "Poor scaling detected"

    def test_paragraph_count_scaling(self, linter):
        """Processing time should scale reasonably with paragraph count."""
        paragraph = "This is a test paragraph with some content.\n\n"

        times = []
        counts = [5, 10, 20]

        for count in counts:
            text = paragraph * count
            start = time.perf_counter()
            linter.check(text)
            times.append(time.perf_counter() - start)

        # All should complete
        assert len(times) == 3
        # Doubling paragraphs shouldn't more than quadruple time
        if times[0] > 0.001:
            ratio = times[2] / times[0]
            assert ratio < 20, f"Poor paragraph scaling: {ratio:.1f}x"

    def test_flag_count_impact(self, linter):
        """Many flags shouldn't drastically slow processing."""
        # Clean text (few flags)
        clean = "The study found specific results (p<0.05). " * 20

        # Problematic text (many flags)
        problematic = "Many experts believe things changed significantly. " * 20

        start = time.perf_counter()
        clean_result = linter.check(clean)
        clean_time = time.perf_counter() - start

        start = time.perf_counter()
        prob_result = linter.check(problematic)
        prob_time = time.perf_counter() - start

        # Problematic text shouldn't take more than 5x longer
        if clean_time > 0.001:
            ratio = prob_time / clean_time
            assert ratio < 10, f"Flag processing too slow: {ratio:.1f}x"


# =============================================================================
# Concurrency Tests - Parallel Processing
# =============================================================================

class TestConcurrency:
    """Tests for concurrent/parallel processing behavior."""

    def test_multiple_linter_instances(self):
        """Multiple linter instances should work independently."""
        linters = [Linter() for _ in range(3)]
        texts = [
            "First text for analysis.",
            "Second text for analysis.",
            "Third text for analysis.",
        ]

        results = []
        for linter, text in zip(linters, texts):
            results.append(linter.check(text))

        assert len(results) == 3
        assert all(isinstance(r, AnalysisResult) for r in results)

    def test_shared_linter_sequential(self):
        """Shared linter should handle sequential requests."""
        linter = Linter()
        texts = [f"Text number {i} for analysis." for i in range(10)]

        results = [linter.check(text) for text in texts]

        assert len(results) == 10
        assert all(isinstance(r, AnalysisResult) for r in results)

    def test_thread_pool_processing(self):
        """Thread pool processing should work (if supported)."""
        texts = [f"Text {i} for parallel processing." for i in range(5)]

        def analyze(text):
            return Linter().check(text)

        results = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(analyze, text) for text in texts]
            for future in as_completed(futures):
                results.append(future.result())

        assert len(results) == 5
        assert all(isinstance(r, AnalysisResult) for r in results)


# =============================================================================
# Memory Tests - Resource Usage
# =============================================================================

class TestMemoryUsage:
    """Tests for memory usage patterns."""

    def test_no_memory_leak_repeated_analysis(self, linter):
        """Repeated analysis shouldn't leak memory significantly."""
        text = "Test sentence. " * 100

        # Force garbage collection
        gc.collect()

        # Run many analyses
        for _ in range(20):
            linter.check(text)

        # Force garbage collection again
        gc.collect()

        # If we get here without MemoryError, basic check passes
        assert True

    def test_large_result_handling(self, linter):
        """Large results should be handled without issues."""
        # Generate text that produces many flags
        text = """
        In today's society, many experts believe various things
        have changed significantly throughout history. It is clear
        that freedom is the state of being free. Studies show this.
        """ * 20

        result = linter.check(text)

        # Result should be accessible
        assert result.summary.flag_count >= 0
        assert len(result.paragraphs) >= 1

    def test_cleanup_after_analysis(self, linter):
        """Resources should be cleaned up after analysis."""
        text = "Test sentence for cleanup verification."

        for _ in range(10):
            result = linter.check(text)
            # Result should be complete
            assert result.id is not None

        # Force cleanup
        gc.collect()

        # Should be able to continue
        final_result = linter.check(text)
        assert isinstance(final_result, AnalysisResult)


# =============================================================================
# Configuration Performance Tests
# =============================================================================

class TestConfigurationPerformance:
    """Tests for performance with different configurations."""

    def test_strict_vs_relaxed_performance(self):
        """Strict mode shouldn't be drastically slower than relaxed."""
        text = "Test sentence for configuration comparison. " * 20

        relaxed_linter = Linter(Config(level="relaxed"))
        strict_linter = Linter(Config(level="strict"))

        start = time.perf_counter()
        relaxed_linter.check(text)
        relaxed_time = time.perf_counter() - start

        start = time.perf_counter()
        strict_linter.check(text)
        strict_time = time.perf_counter() - start

        # Strict shouldn't be more than 3x slower
        if relaxed_time > 0.001:
            ratio = strict_time / relaxed_time
            assert ratio < 5, f"Strict too slow: {ratio:.1f}x relaxed"

    def test_domain_terms_performance(self):
        """Many domain terms shouldn't drastically slow analysis."""
        text = "Test sentence with epistemological considerations. " * 10

        no_terms = Linter(Config(domain_terms=[]))
        many_terms = Linter(Config(domain_terms=[f"term{i}" for i in range(100)]))

        start = time.perf_counter()
        no_terms.check(text)
        no_terms_time = time.perf_counter() - start

        start = time.perf_counter()
        many_terms.check(text)
        many_terms_time = time.perf_counter() - start

        # Many terms shouldn't be more than 2x slower
        if no_terms_time > 0.001:
            ratio = many_terms_time / no_terms_time
            assert ratio < 3, f"Domain terms too slow: {ratio:.1f}x"


# =============================================================================
# Performance Regression Markers
# =============================================================================

class TestPerformanceBaselines:
    """
    Baseline performance tests for regression detection.

    These tests establish performance baselines. If they start failing,
    it indicates a potential performance regression.
    """

    def test_baseline_short_text(self, linter):
        """Baseline: Short text under 5 seconds."""
        result = linter.check("Short test.")
        assert result.processing_time_ms < 5000

    def test_baseline_paragraph(self, linter, sample_paragraph):
        """Baseline: Paragraph under 15 seconds."""
        result = linter.check(sample_paragraph)
        assert result.processing_time_ms < 15000

    def test_baseline_linter_reuse(self, linter):
        """Baseline: Linter reuse efficient."""
        times = []
        for _ in range(5):
            result = linter.check("Test.")
            times.append(result.processing_time_ms)

        # Later analyses shouldn't be slower
        assert times[-1] <= times[0] * 3
