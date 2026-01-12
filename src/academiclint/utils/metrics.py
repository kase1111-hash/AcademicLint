"""Telemetry and metrics collection for AcademicLint.

This module provides instrumentation for collecting usage metrics,
performance data, and operational telemetry.

Features:
- Counter, Gauge, Histogram, and Timer metrics
- Thread-safe collection
- Multiple export formats (JSON, Prometheus)
- Configurable sampling and aggregation
- Privacy-respecting (no PII collection)

Usage:
    from academiclint.utils.metrics import metrics, Timer

    # Count events
    metrics.increment("analysis.requests")

    # Track values
    metrics.gauge("active_sessions", 5)

    # Record distributions
    metrics.histogram("text.length", len(text))

    # Time operations
    with Timer("analysis.duration"):
        result = linter.analyze(text)

    # Export metrics
    data = metrics.export_json()
"""

import json
import logging
import os
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """Container for a metric value with metadata."""

    value: float
    timestamp: float = field(default_factory=time.time)
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class HistogramBucket:
    """Histogram bucket for distribution tracking."""

    le: float  # Less than or equal boundary
    count: int = 0


class Counter:
    """Thread-safe counter metric."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._value = 0.0
        self._lock = threading.Lock()
        self._labels: dict[tuple, float] = defaultdict(float)

    def inc(self, value: float = 1.0, **labels: str) -> None:
        """Increment the counter."""
        with self._lock:
            if labels:
                key = tuple(sorted(labels.items()))
                self._labels[key] += value
            else:
                self._value += value

    def get(self, **labels: str) -> float:
        """Get current counter value."""
        with self._lock:
            if labels:
                key = tuple(sorted(labels.items()))
                return self._labels.get(key, 0.0)
            return self._value

    def reset(self) -> None:
        """Reset counter to zero."""
        with self._lock:
            self._value = 0.0
            self._labels.clear()


class Gauge:
    """Thread-safe gauge metric for values that can go up and down."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._value = 0.0
        self._lock = threading.Lock()
        self._labels: dict[tuple, float] = {}

    def set(self, value: float, **labels: str) -> None:
        """Set the gauge value."""
        with self._lock:
            if labels:
                key = tuple(sorted(labels.items()))
                self._labels[key] = value
            else:
                self._value = value

    def inc(self, value: float = 1.0, **labels: str) -> None:
        """Increment the gauge."""
        with self._lock:
            if labels:
                key = tuple(sorted(labels.items()))
                self._labels[key] = self._labels.get(key, 0.0) + value
            else:
                self._value += value

    def dec(self, value: float = 1.0, **labels: str) -> None:
        """Decrement the gauge."""
        self.inc(-value, **labels)

    def get(self, **labels: str) -> float:
        """Get current gauge value."""
        with self._lock:
            if labels:
                key = tuple(sorted(labels.items()))
                return self._labels.get(key, 0.0)
            return self._value


class Histogram:
    """Thread-safe histogram for tracking value distributions."""

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: tuple[float, ...] = DEFAULT_BUCKETS,
    ):
        self.name = name
        self.description = description
        self._buckets = sorted(buckets)
        self._lock = threading.Lock()
        self._counts: list[int] = [0] * len(self._buckets)
        self._sum = 0.0
        self._count = 0

    def observe(self, value: float) -> None:
        """Record a value in the histogram."""
        with self._lock:
            self._sum += value
            self._count += 1
            for i, bucket in enumerate(self._buckets):
                if value <= bucket:
                    self._counts[i] += 1

    def get_buckets(self) -> list[tuple[float, int]]:
        """Get bucket boundaries and counts."""
        with self._lock:
            return list(zip(self._buckets, self._counts))

    def get_sum(self) -> float:
        """Get sum of all observed values."""
        with self._lock:
            return self._sum

    def get_count(self) -> int:
        """Get count of observations."""
        with self._lock:
            return self._count

    def get_mean(self) -> float:
        """Get mean of observed values."""
        with self._lock:
            return self._sum / self._count if self._count > 0 else 0.0


class Timer:
    """Context manager for timing operations."""

    def __init__(self, name: str, metrics_registry: Optional["MetricsRegistry"] = None):
        self.name = name
        self._registry = metrics_registry
        self._start: Optional[float] = None
        self._duration: Optional[float] = None

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        if self._start is not None:
            self._duration = time.perf_counter() - self._start
            if self._registry:
                self._registry.histogram(self.name, self._duration)

    @property
    def duration(self) -> Optional[float]:
        """Get the measured duration in seconds."""
        return self._duration


class MetricsRegistry:
    """Central registry for all metrics.

    Thread-safe collection and export of metrics.
    """

    def __init__(self, enabled: bool = True, prefix: str = "academiclint"):
        self._enabled = enabled
        self._prefix = prefix
        self._lock = threading.Lock()
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._start_time = time.time()

        # Initialize default metrics
        self._init_default_metrics()

    def _init_default_metrics(self) -> None:
        """Initialize default application metrics."""
        self.counter("info", "Application info metric")
        self.gauge("uptime_seconds", "Application uptime in seconds")

    def _full_name(self, name: str) -> str:
        """Get full metric name with prefix."""
        return f"{self._prefix}_{name}" if self._prefix else name

    @property
    def enabled(self) -> bool:
        """Check if metrics collection is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable metrics collection."""
        self._enabled = True

    def disable(self) -> None:
        """Disable metrics collection."""
        self._enabled = False

    def counter(self, name: str, description: str = "") -> Counter:
        """Get or create a counter metric."""
        full_name = self._full_name(name)
        with self._lock:
            if full_name not in self._counters:
                self._counters[full_name] = Counter(full_name, description)
            return self._counters[full_name]

    def gauge(self, name: str, description: str = "") -> Gauge:
        """Get or create a gauge metric."""
        full_name = self._full_name(name)
        with self._lock:
            if full_name not in self._gauges:
                self._gauges[full_name] = Gauge(full_name, description)
            return self._gauges[full_name]

    def histogram(
        self,
        name: str,
        value: Optional[float] = None,
        description: str = "",
        buckets: tuple[float, ...] = Histogram.DEFAULT_BUCKETS,
    ) -> Histogram:
        """Get or create a histogram metric, optionally recording a value."""
        full_name = self._full_name(name)
        with self._lock:
            if full_name not in self._histograms:
                self._histograms[full_name] = Histogram(full_name, description, buckets)
            hist = self._histograms[full_name]

        if value is not None and self._enabled:
            hist.observe(value)

        return hist

    def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
        """Increment a counter."""
        if self._enabled:
            self.counter(name).inc(value, **labels)

    def set_gauge(self, name: str, value: float, **labels: str) -> None:
        """Set a gauge value."""
        if self._enabled:
            self.gauge(name).set(value, **labels)

    def timer(self, name: str) -> Timer:
        """Create a timer context manager."""
        return Timer(name, self if self._enabled else None)

    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self._start_time

    def export_dict(self) -> dict[str, Any]:
        """Export all metrics as a dictionary."""
        with self._lock:
            # Update uptime
            self.set_gauge("uptime_seconds", self.get_uptime())

            result: dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": self.get_uptime(),
                "counters": {},
                "gauges": {},
                "histograms": {},
            }

            for name, counter in self._counters.items():
                result["counters"][name] = counter.get()

            for name, gauge in self._gauges.items():
                result["gauges"][name] = gauge.get()

            for name, histogram in self._histograms.items():
                result["histograms"][name] = {
                    "count": histogram.get_count(),
                    "sum": histogram.get_sum(),
                    "mean": histogram.get_mean(),
                    "buckets": histogram.get_buckets(),
                }

            return result

    def export_json(self, indent: int = 2) -> str:
        """Export all metrics as JSON string."""
        return json.dumps(self.export_dict(), indent=indent)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines: list[str] = []

        with self._lock:
            # Update uptime
            self.set_gauge("uptime_seconds", self.get_uptime())

            # Export counters
            for name, counter in self._counters.items():
                if counter.description:
                    lines.append(f"# HELP {name} {counter.description}")
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {counter.get()}")

            # Export gauges
            for name, gauge in self._gauges.items():
                if gauge.description:
                    lines.append(f"# HELP {name} {gauge.description}")
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {gauge.get()}")

            # Export histograms
            for name, histogram in self._histograms.items():
                if histogram.description:
                    lines.append(f"# HELP {name} {histogram.description}")
                lines.append(f"# TYPE {name} histogram")

                for le, count in histogram.get_buckets():
                    lines.append(f'{name}_bucket{{le="{le}"}} {count}')
                lines.append(f'{name}_bucket{{le="+Inf"}} {histogram.get_count()}')
                lines.append(f"{name}_sum {histogram.get_sum()}")
                lines.append(f"{name}_count {histogram.get_count()}")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            for counter in self._counters.values():
                counter.reset()
            self._gauges.clear()
            self._histograms.clear()
            self._start_time = time.time()
            self._init_default_metrics()


# Global metrics registry
_metrics: Optional[MetricsRegistry] = None
_metrics_lock = threading.Lock()


def get_metrics() -> MetricsRegistry:
    """Get the global metrics registry.

    Returns:
        Global MetricsRegistry instance
    """
    global _metrics

    if _metrics is None:
        with _metrics_lock:
            if _metrics is None:
                # Check environment for enabled status
                enabled = os.environ.get("ACADEMICLINT_METRICS_ENABLED", "true").lower() == "true"
                _metrics = MetricsRegistry(enabled=enabled)

    return _metrics


def reset_metrics() -> None:
    """Reset the global metrics registry."""
    global _metrics
    with _metrics_lock:
        if _metrics:
            _metrics.reset()


# Convenience functions using global registry
def increment(name: str, value: float = 1.0, **labels: str) -> None:
    """Increment a counter in the global registry."""
    get_metrics().increment(name, value, **labels)


def set_gauge(name: str, value: float, **labels: str) -> None:
    """Set a gauge value in the global registry."""
    get_metrics().set_gauge(name, value, **labels)


def histogram(name: str, value: float) -> None:
    """Record a histogram value in the global registry."""
    get_metrics().histogram(name, value)


def timer(name: str) -> Timer:
    """Create a timer using the global registry."""
    return get_metrics().timer(name)


@contextmanager
def timed(name: str):
    """Context manager for timing with the global registry."""
    with get_metrics().timer(name) as t:
        yield t


def record_analysis(
    text_length: int,
    duration_seconds: float,
    flag_count: int,
    density_score: float,
) -> None:
    """Record metrics for an analysis operation.

    Args:
        text_length: Length of analyzed text
        duration_seconds: Analysis duration in seconds
        flag_count: Number of flags raised
        density_score: Semantic density score
    """
    m = get_metrics()
    m.increment("analysis_total")
    m.histogram("analysis_duration_seconds", duration_seconds)
    m.histogram("analysis_text_length", text_length)
    m.histogram("analysis_flag_count", flag_count)
    m.histogram("analysis_density_score", density_score)


def record_error(error_type: str) -> None:
    """Record an error occurrence.

    Args:
        error_type: Type/category of error
    """
    get_metrics().increment("errors_total", error_type=error_type)


def record_api_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    """Record metrics for an API request.

    Args:
        method: HTTP method
        endpoint: API endpoint path
        status_code: Response status code
        duration_seconds: Request duration in seconds
    """
    m = get_metrics()
    m.increment("api_requests_total", method=method, endpoint=endpoint)
    m.histogram("api_request_duration_seconds", duration_seconds)

    if status_code >= 400:
        m.increment("api_errors_total", method=method, status_code=str(status_code))


# Decorator for timing functions
def timed_function(name: Optional[str] = None) -> Callable:
    """Decorator to time function execution.

    Args:
        name: Metric name (defaults to function name)

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        metric_name = name or f"function_{func.__name__}_duration_seconds"

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with timer(metric_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator
