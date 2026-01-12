# Semantic Versioning

AcademicLint follows [Semantic Versioning 2.0.0](https://semver.org/).

## Version Format

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

| Component | Description | Example |
|-----------|-------------|---------|
| MAJOR | Breaking API changes | `2.0.0` |
| MINOR | New features, backwards-compatible | `1.1.0` |
| PATCH | Bug fixes, backwards-compatible | `1.0.1` |
| PRERELEASE | Pre-release identifier | `1.0.0-alpha` |
| BUILD | Build metadata | `1.0.0+20240115` |

## Version Lifecycle

### Development (0.x.x)

During initial development, the API may change at any time:
- `0.1.0` - Initial release
- `0.2.0` - New features (may break API)
- `0.2.1` - Bug fixes

### Stable (1.x.x+)

After reaching 1.0.0, the API is stable:
- **MAJOR** bump: Breaking changes that require code updates
- **MINOR** bump: New features that are backwards-compatible
- **PATCH** bump: Bug fixes only

## Pre-release Versions

| Identifier | Stage | Example |
|------------|-------|---------|
| `alpha` | Early testing, unstable | `1.0.0-alpha` |
| `beta` | Feature complete, testing | `1.0.0-beta.1` |
| `rc` | Release candidate | `1.0.0-rc.1` |

## Bumping Versions

Use the provided scripts to bump versions:

```bash
# Show current version
make version

# Bump patch version (0.1.0 -> 0.1.1)
make bump-patch

# Bump minor version (0.1.0 -> 0.2.0)
make bump-minor

# Bump major version (0.1.0 -> 1.0.0)
make bump-major

# Set specific version
make bump-set VERSION=1.2.3

# Preview changes without applying
make bump-dry-run
```

Or use the script directly:

```bash
python scripts/bump_version.py patch
python scripts/bump_version.py minor
python scripts/bump_version.py major
python scripts/bump_version.py set 1.2.3
python scripts/bump_version.py show
```

## Files Updated

The bump script updates version in:
- `pyproject.toml` - Package version
- `src/academiclint/__init__.py` - Module version
- `src/academiclint/version.py` - Version utilities
- `Dockerfile` - Container image label

## Release Process

1. **Update version:**
   ```bash
   make bump-minor  # or patch/major
   ```

2. **Commit the change:**
   ```bash
   git add -A
   git commit -m "Bump version to X.Y.Z"
   ```

3. **Create annotated tag:**
   ```bash
   git tag -a vX.Y.Z -m "Release X.Y.Z"
   ```

4. **Push with tags:**
   ```bash
   git push origin main --tags
   ```

5. **GitHub Actions** will automatically:
   - Run tests
   - Build packages
   - Publish to PyPI (for stable releases)
   - Create GitHub Release

## Programmatic Access

```python
from academiclint import __version__

# Simple string
print(__version__)  # "0.1.0"

# Detailed version info
from academiclint.version import get_version_info

version = get_version_info()
print(version.major)       # 0
print(version.minor)       # 1
print(version.patch)       # 0
print(version.is_stable)   # False (major < 1)

# Version comparison
from academiclint.version import Version

v1 = Version.parse("1.0.0")
v2 = Version.parse("1.1.0")
print(v1 < v2)  # True

# Compatibility check
from academiclint.version import is_compatible

is_compatible("0.1.0")  # Check against current version
```

## Deprecation Policy

1. Features are deprecated with a warning in a **MINOR** release
2. Deprecated features are removed in the next **MAJOR** release
3. Deprecation warnings include migration instructions
4. Minimum deprecation period: 2 minor releases

## API Stability Guarantees

### Stable API (will not break in minor/patch releases)
- `Linter` class and its public methods
- `Config` and `OutputConfig` classes
- `AnalysisResult`, `Flag`, `FlagType`, `Severity`
- CLI interface and exit codes
- JSON output format

### Internal API (may change without notice)
- Anything in `_private` modules
- Detector internals
- Parser implementation details
- Internal utility functions
