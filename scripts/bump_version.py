#!/usr/bin/env python3
"""Version bumping utility for AcademicLint.

This script updates version numbers across all project files following
Semantic Versioning 2.0.0 (https://semver.org/).

Usage:
    python scripts/bump_version.py major    # 0.1.0 -> 1.0.0
    python scripts/bump_version.py minor    # 0.1.0 -> 0.2.0
    python scripts/bump_version.py patch    # 0.1.0 -> 0.1.1
    python scripts/bump_version.py set 1.2.3    # Set specific version
    python scripts/bump_version.py show     # Show current version

Files updated:
    - pyproject.toml
    - src/academiclint/__init__.py
    - src/academiclint/version.py
    - Dockerfile (LABEL version)
"""

import argparse
import re
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent


def read_file(path: Path) -> str:
    """Read file contents."""
    return path.read_text(encoding="utf-8")


def write_file(path: Path, content: str) -> None:
    """Write file contents."""
    path.write_text(content, encoding="utf-8")


def get_current_version(root: Path) -> str:
    """Get current version from pyproject.toml."""
    pyproject = root / "pyproject.toml"
    content = read_file(pyproject)

    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")

    return match.group(1)


def parse_version(version: str) -> tuple[int, int, int, str | None]:
    """Parse version string into components."""
    # Handle prerelease suffix
    prerelease = None
    if "-" in version:
        version, prerelease = version.split("-", 1)

    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")

    return int(parts[0]), int(parts[1]), int(parts[2]), prerelease


def format_version(major: int, minor: int, patch: int, prerelease: str | None = None) -> str:
    """Format version components into string."""
    version = f"{major}.{minor}.{patch}"
    if prerelease:
        version += f"-{prerelease}"
    return version


def bump_version(current: str, bump_type: str) -> str:
    """Calculate new version based on bump type."""
    major, minor, patch, _ = parse_version(current)

    if bump_type == "major":
        return format_version(major + 1, 0, 0)
    elif bump_type == "minor":
        return format_version(major, minor + 1, 0)
    elif bump_type == "patch":
        return format_version(major, minor, patch + 1)
    else:
        raise ValueError(f"Unknown bump type: {bump_type}")


def update_pyproject(root: Path, old_version: str, new_version: str) -> bool:
    """Update version in pyproject.toml."""
    path = root / "pyproject.toml"
    content = read_file(path)

    new_content = re.sub(
        rf'^version\s*=\s*"{re.escape(old_version)}"',
        f'version = "{new_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )

    if new_content != content:
        write_file(path, new_content)
        return True
    return False


def update_init(root: Path, old_version: str, new_version: str) -> bool:
    """Update version in __init__.py."""
    path = root / "src" / "academiclint" / "__init__.py"
    content = read_file(path)

    new_content = re.sub(
        rf'^__version__\s*=\s*"{re.escape(old_version)}"',
        f'__version__ = "{new_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )

    if new_content != content:
        write_file(path, new_content)
        return True
    return False


def update_version_module(root: Path, old_version: str, new_version: str) -> bool:
    """Update version in version.py."""
    path = root / "src" / "academiclint" / "version.py"
    if not path.exists():
        return False

    content = read_file(path)
    major, minor, patch, _ = parse_version(new_version)

    # Update __version__
    new_content = re.sub(
        rf'^__version__\s*=\s*"{re.escape(old_version)}"',
        f'__version__ = "{new_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )

    # Update VERSION_MAJOR
    new_content = re.sub(
        r"^VERSION_MAJOR\s*=\s*\d+",
        f"VERSION_MAJOR = {major}",
        new_content,
        count=1,
        flags=re.MULTILINE,
    )

    # Update VERSION_MINOR
    new_content = re.sub(
        r"^VERSION_MINOR\s*=\s*\d+",
        f"VERSION_MINOR = {minor}",
        new_content,
        count=1,
        flags=re.MULTILINE,
    )

    # Update VERSION_PATCH
    new_content = re.sub(
        r"^VERSION_PATCH\s*=\s*\d+",
        f"VERSION_PATCH = {patch}",
        new_content,
        count=1,
        flags=re.MULTILINE,
    )

    if new_content != content:
        write_file(path, new_content)
        return True
    return False


def update_dockerfile(root: Path, old_version: str, new_version: str) -> bool:
    """Update version in Dockerfile."""
    path = root / "Dockerfile"
    if not path.exists():
        return False

    content = read_file(path)

    new_content = re.sub(
        rf'^LABEL\s+version\s*=\s*"{re.escape(old_version)}"',
        f'LABEL version="{new_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )

    if new_content != content:
        write_file(path, new_content)
        return True
    return False


def update_all_files(root: Path, old_version: str, new_version: str) -> list[str]:
    """Update version in all project files."""
    updated = []

    if update_pyproject(root, old_version, new_version):
        updated.append("pyproject.toml")

    if update_init(root, old_version, new_version):
        updated.append("src/academiclint/__init__.py")

    if update_version_module(root, old_version, new_version):
        updated.append("src/academiclint/version.py")

    if update_dockerfile(root, old_version, new_version):
        updated.append("Dockerfile")

    return updated


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bump version following Semantic Versioning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s major          # 0.1.0 -> 1.0.0
    %(prog)s minor          # 0.1.0 -> 0.2.0
    %(prog)s patch          # 0.1.0 -> 0.1.1
    %(prog)s set 1.2.3      # Set to specific version
    %(prog)s show           # Show current version
        """,
    )

    parser.add_argument(
        "action",
        choices=["major", "minor", "patch", "set", "show"],
        help="Version bump type or action",
    )

    parser.add_argument(
        "version",
        nargs="?",
        help="Version to set (only for 'set' action)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )

    args = parser.parse_args()
    root = get_project_root()

    try:
        current = get_current_version(root)
    except Exception as e:
        print(f"Error reading current version: {e}", file=sys.stderr)
        return 1

    if args.action == "show":
        print(f"Current version: {current}")
        return 0

    if args.action == "set":
        if not args.version:
            print("Error: 'set' action requires a version argument", file=sys.stderr)
            return 1
        try:
            # Validate version format
            parse_version(args.version)
            new_version = args.version
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        new_version = bump_version(current, args.action)

    print(f"Version: {current} -> {new_version}")

    if args.dry_run:
        print("\n[Dry run] Would update:")
        print("  - pyproject.toml")
        print("  - src/academiclint/__init__.py")
        print("  - src/academiclint/version.py")
        print("  - Dockerfile")
        return 0

    updated = update_all_files(root, current, new_version)

    if updated:
        print("\nUpdated files:")
        for file in updated:
            print(f"  - {file}")
        print(f"\nVersion bumped to {new_version}")
        print("\nNext steps:")
        print(f"  1. git add -A")
        print(f"  2. git commit -m 'Bump version to {new_version}'")
        print(f"  3. git tag -a v{new_version} -m 'Release {new_version}'")
        print(f"  4. git push origin main --tags")
    else:
        print("No files were updated")

    return 0


if __name__ == "__main__":
    sys.exit(main())
