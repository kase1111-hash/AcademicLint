"""Pytest configuration and fixtures for AcademicLint tests."""

import pytest

from academiclint import Config, Linter


@pytest.fixture
def default_config():
    """Create a default configuration."""
    return Config()


@pytest.fixture
def strict_config():
    """Create a strict configuration."""
    return Config(level="strict", min_density=0.65)


@pytest.fixture
def linter(default_config):
    """Create a linter with default configuration."""
    return Linter(default_config)


@pytest.fixture
def sample_good_text():
    """Sample text with high clarity."""
    return """
    Smartphone-based messaging has reduced response latency in personal
    communication from hours (email) to minutes (SMS/chat), while
    simultaneously decreasing average message length from 150+ words
    to under 20 (Pew Research, 2023). This compression correlates with
    reported declines in perceived conversation depth (Thompson et al., 2022),
    though causation remains unestablished.
    """


@pytest.fixture
def sample_bad_text():
    """Sample text with low clarity."""
    return """
    In today's society, technology has had a significant impact on
    the way people communicate. Many experts believe this has led
    to both positive and negative outcomes. It is clear that more
    research is needed to fully understand these complex dynamics.
    """


@pytest.fixture
def sample_circular_text():
    """Sample text with circular definitions."""
    return """
    Freedom is the state of being free from oppression.
    Democracy means a democratic form of government.
    """


@pytest.fixture
def sample_causal_text():
    """Sample text with unsupported causal claims."""
    return """
    Social media causes depression in teenagers.
    The policy led to significant changes in the economy.
    """
