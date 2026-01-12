"""Semantic versioning utilities for AcademicLint.

This module provides version information and utilities following
Semantic Versioning 2.0.0 (https://semver.org/).

Version Format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

- MAJOR: Incompatible API changes
- MINOR: Backwards-compatible new functionality
- PATCH: Backwards-compatible bug fixes
- PRERELEASE: Optional pre-release identifier (alpha, beta, rc)
- BUILD: Optional build metadata

Examples:
    0.1.0       - Initial development release
    1.0.0       - First stable release
    1.1.0       - New feature added
    1.1.1       - Bug fix
    2.0.0-alpha - Pre-release of next major version
    2.0.0-rc.1  - Release candidate
"""

import re
from dataclasses import dataclass
from typing import Optional

# Single source of truth for version
__version__ = "0.1.0"

# Version components
VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_PATCH = 0
VERSION_PRERELEASE: Optional[str] = None
VERSION_BUILD: Optional[str] = None

# Semantic version regex pattern
SEMVER_PATTERN = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


@dataclass(frozen=True, order=True)
class Version:
    """Semantic version representation.

    Supports comparison operations following semver precedence rules.

    Attributes:
        major: Major version number (breaking changes)
        minor: Minor version number (new features)
        patch: Patch version number (bug fixes)
        prerelease: Pre-release identifier (e.g., "alpha", "beta.1")
        build: Build metadata (ignored in comparisons)
    """

    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate version components."""
        if self.major < 0 or self.minor < 0 or self.patch < 0:
            raise ValueError("Version numbers must be non-negative")

    def __str__(self) -> str:
        """Return version string."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"Version({self})"

    @classmethod
    def parse(cls, version_string: str) -> "Version":
        """Parse a version string into a Version object.

        Args:
            version_string: Semantic version string (e.g., "1.2.3-alpha+build")

        Returns:
            Version object

        Raises:
            ValueError: If the version string is invalid
        """
        # Strip 'v' prefix if present
        if version_string.startswith("v"):
            version_string = version_string[1:]

        match = SEMVER_PATTERN.match(version_string)
        if not match:
            raise ValueError(f"Invalid semantic version: {version_string}")

        return cls(
            major=int(match.group("major")),
            minor=int(match.group("minor")),
            patch=int(match.group("patch")),
            prerelease=match.group("prerelease"),
            build=match.group("build"),
        )

    @property
    def is_prerelease(self) -> bool:
        """Check if this is a pre-release version."""
        return self.prerelease is not None

    @property
    def is_stable(self) -> bool:
        """Check if this is a stable release (major >= 1, no prerelease)."""
        return self.major >= 1 and not self.is_prerelease

    @property
    def public_version(self) -> str:
        """Return version without build metadata."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        return version

    def bump_major(self) -> "Version":
        """Return new version with major incremented."""
        return Version(major=self.major + 1, minor=0, patch=0)

    def bump_minor(self) -> "Version":
        """Return new version with minor incremented."""
        return Version(major=self.major, minor=self.minor + 1, patch=0)

    def bump_patch(self) -> "Version":
        """Return new version with patch incremented."""
        return Version(major=self.major, minor=self.minor, patch=self.patch + 1)

    def with_prerelease(self, prerelease: str) -> "Version":
        """Return new version with prerelease set."""
        return Version(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            prerelease=prerelease,
            build=self.build,
        )

    def with_build(self, build: str) -> "Version":
        """Return new version with build metadata set."""
        return Version(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            prerelease=self.prerelease,
            build=build,
        )


def get_version() -> str:
    """Get the current version string.

    Returns:
        Current version as a string
    """
    return __version__


def get_version_info() -> Version:
    """Get the current version as a Version object.

    Returns:
        Current version as Version object
    """
    return Version.parse(__version__)


def get_version_tuple() -> tuple[int, int, int]:
    """Get the current version as a tuple.

    Returns:
        Tuple of (major, minor, patch)
    """
    return (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)


# Version compatibility checks
def is_compatible(required: str, current: Optional[str] = None) -> bool:
    """Check if the current version is compatible with the required version.

    Uses caret (^) compatibility: same major version, minor >= required.

    Args:
        required: Required version string
        current: Current version (defaults to package version)

    Returns:
        True if compatible, False otherwise
    """
    if current is None:
        current = __version__

    required_v = Version.parse(required)
    current_v = Version.parse(current)

    # Major version must match
    if required_v.major != current_v.major:
        return False

    # For 0.x versions, minor must also match (API unstable)
    if required_v.major == 0:
        return required_v.minor == current_v.minor

    # For 1.x+, current minor must be >= required
    return current_v.minor >= required_v.minor
