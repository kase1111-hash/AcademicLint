#!/usr/bin/env bash
# =============================================================================
# AcademicLint Packaging Script
# =============================================================================
# Builds distributable packages in various formats:
#   - Python wheel and sdist
#   - Docker images (production, development, API)
#   - Standalone zip archive
#
# Usage:
#   ./scripts/package.sh [target]
#
# Targets:
#   all       - Build all package types (default)
#   wheel     - Build Python wheel and source distribution
#   docker    - Build Docker images
#   zip       - Create standalone zip archive
#   clean     - Remove build artifacts
# =============================================================================

set -euo pipefail

# Configuration
PROJECT_NAME="academiclint"
VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])" 2>/dev/null || echo "0.1.0")
BUILD_DIR="dist"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
DOCKER_TAG="${DOCKER_TAG:-${VERSION}}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check requirements
check_requirements() {
    log_info "Checking requirements..."

    local missing=()

    if ! command -v python &> /dev/null; then
        missing+=("python")
    fi

    if ! command -v pip &> /dev/null; then
        missing+=("pip")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        exit 1
    fi

    # Ensure build tools are installed
    pip install --quiet build twine

    log_success "All requirements met"
}

# Build Python wheel and source distribution
build_wheel() {
    log_info "Building Python wheel and source distribution..."

    # Clean previous builds
    rm -rf build/ "${BUILD_DIR}/"*.whl "${BUILD_DIR}/"*.tar.gz

    # Build wheel and sdist
    python -m build

    # Verify the build
    python -m twine check "${BUILD_DIR}"/*

    log_success "Built packages:"
    ls -la "${BUILD_DIR}/"*.whl "${BUILD_DIR}/"*.tar.gz 2>/dev/null || true
}

# Build Docker images
build_docker() {
    log_info "Building Docker images..."

    if ! command -v docker &> /dev/null; then
        log_warn "Docker not available, skipping Docker build"
        return 0
    fi

    local prefix=""
    if [[ -n "${DOCKER_REGISTRY}" ]]; then
        prefix="${DOCKER_REGISTRY}/"
    fi

    # Build production image
    log_info "Building production image..."
    docker build \
        --target production \
        --tag "${prefix}${PROJECT_NAME}:${DOCKER_TAG}" \
        --tag "${prefix}${PROJECT_NAME}:latest" \
        .

    # Build API image
    log_info "Building API server image..."
    docker build \
        --target api \
        --tag "${prefix}${PROJECT_NAME}:${DOCKER_TAG}-api" \
        --tag "${prefix}${PROJECT_NAME}:api" \
        .

    # Build development image
    log_info "Building development image..."
    docker build \
        --target development \
        --tag "${prefix}${PROJECT_NAME}:${DOCKER_TAG}-dev" \
        --tag "${prefix}${PROJECT_NAME}:dev" \
        .

    log_success "Docker images built:"
    docker images "${prefix}${PROJECT_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
}

# Create standalone zip archive
build_zip() {
    log_info "Creating standalone zip archive..."

    local zip_name="${PROJECT_NAME}-${VERSION}"
    local zip_dir="${BUILD_DIR}/${zip_name}"
    local zip_file="${BUILD_DIR}/${zip_name}.zip"

    # Clean previous archive
    rm -rf "${zip_dir}" "${zip_file}"

    # Create archive directory
    mkdir -p "${zip_dir}"

    # Copy source files
    cp -r src/ "${zip_dir}/"
    cp -r config/ "${zip_dir}/"
    cp pyproject.toml "${zip_dir}/"
    cp README.md "${zip_dir}/"
    cp LICENSE* "${zip_dir}/" 2>/dev/null || true

    # Create requirements file from pyproject.toml
    pip install --quiet toml
    python -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
deps = data.get('project', {}).get('dependencies', [])
with open('${zip_dir}/requirements.txt', 'w') as f:
    f.write('\\n'.join(deps))
"

    # Create install script
    cat > "${zip_dir}/install.sh" << 'INSTALL_EOF'
#!/usr/bin/env bash
# AcademicLint Installation Script
set -e
echo "Installing AcademicLint..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -m spacy download en_core_web_sm
echo "Installation complete!"
echo "Run 'python -m academiclint --help' to get started."
INSTALL_EOF
    chmod +x "${zip_dir}/install.sh"

    # Create Windows install script
    cat > "${zip_dir}/install.bat" << 'INSTALL_BAT_EOF'
@echo off
REM AcademicLint Installation Script for Windows
echo Installing AcademicLint...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -m spacy download en_core_web_sm
echo Installation complete!
echo Run 'python -m academiclint --help' to get started.
pause
INSTALL_BAT_EOF

    # Create zip archive
    cd "${BUILD_DIR}"
    zip -r "${zip_name}.zip" "${zip_name}"
    cd - > /dev/null

    # Clean up directory
    rm -rf "${zip_dir}"

    log_success "Created zip archive: ${zip_file}"
    ls -la "${zip_file}"
}

# Clean build artifacts
clean() {
    log_info "Cleaning build artifacts..."

    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    rm -rf src/*.egg-info/
    rm -rf .eggs/
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true

    log_success "Build artifacts cleaned"
}

# Build all packages
build_all() {
    check_requirements
    build_wheel
    build_docker
    build_zip

    echo ""
    log_success "All packages built successfully!"
    echo ""
    echo "Artifacts:"
    echo "  - Python packages: dist/*.whl, dist/*.tar.gz"
    echo "  - Docker images: ${PROJECT_NAME}:${DOCKER_TAG}, ${PROJECT_NAME}:api, ${PROJECT_NAME}:dev"
    echo "  - Zip archive: dist/${PROJECT_NAME}-${VERSION}.zip"
}

# Main entry point
main() {
    local target="${1:-all}"

    echo "=============================================="
    echo " AcademicLint Packaging Script v${VERSION}"
    echo "=============================================="
    echo ""

    case "${target}" in
        all)
            build_all
            ;;
        wheel)
            check_requirements
            build_wheel
            ;;
        docker)
            build_docker
            ;;
        zip)
            check_requirements
            build_zip
            ;;
        clean)
            clean
            ;;
        *)
            echo "Usage: $0 [all|wheel|docker|zip|clean]"
            exit 1
            ;;
    esac
}

main "$@"
