#!/usr/bin/env bash
# =============================================================================
# AcademicLint Build Script
# =============================================================================
# Comprehensive build script for building, testing, and packaging
#
# Usage:
#   ./scripts/build.sh [command]
#
# Commands:
#   install     - Install dependencies
#   test        - Run tests
#   lint        - Run linting
#   build       - Build packages
#   clean       - Clean artifacts
#   ci          - Run full CI pipeline
#   release     - Prepare release
#   help        - Show help
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project settings
PACKAGE="academiclint"
SRC_DIR="src/${PACKAGE}"
TEST_DIR="tests"

# =============================================================================
# Helper Functions
# =============================================================================

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

check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
}

# =============================================================================
# Commands
# =============================================================================

cmd_install() {
    log_info "Installing dependencies..."

    if [[ "$1" == "dev" ]]; then
        pip install -e ".[dev]"
        log_info "Installing spaCy model..."
        python3 -m spacy download en_core_web_sm || true
        log_info "Installing pre-commit hooks..."
        pre-commit install || true
    elif [[ "$1" == "all" ]]; then
        pip install -e ".[all]"
    else
        pip install -e .
    fi

    log_success "Installation complete!"
}

cmd_test() {
    log_info "Running tests..."

    case "$1" in
        unit)
            pytest ${TEST_DIR} -v --ignore=${TEST_DIR}/test_integration_linter.py \
                --ignore=${TEST_DIR}/test_integration_api.py \
                --ignore=${TEST_DIR}/test_acceptance.py \
                --ignore=${TEST_DIR}/test_performance.py \
                --ignore=${TEST_DIR}/test_security.py
            ;;
        integration)
            pytest ${TEST_DIR}/test_integration_*.py -v
            ;;
        acceptance)
            pytest ${TEST_DIR}/test_acceptance.py -v
            ;;
        performance)
            pytest ${TEST_DIR}/test_performance.py -v --timeout=300
            ;;
        security)
            pytest ${TEST_DIR}/test_security.py -v
            ;;
        coverage)
            pytest ${TEST_DIR} --cov=${SRC_DIR} --cov-report=term-missing --cov-report=html
            ;;
        *)
            pytest ${TEST_DIR} -v
            ;;
    esac

    log_success "Tests complete!"
}

cmd_lint() {
    log_info "Running linting..."

    local FIX=""
    if [[ "$1" == "--fix" ]]; then
        FIX="--fix"
    fi

    ruff check ${SRC_DIR} ${FIX}
    ruff check ${TEST_DIR} ${FIX}

    log_success "Linting complete!"
}

cmd_format() {
    log_info "Formatting code..."

    if [[ "$1" == "--check" ]]; then
        ruff format --check ${SRC_DIR}
        ruff format --check ${TEST_DIR}
    else
        ruff format ${SRC_DIR}
        ruff format ${TEST_DIR}
    fi

    log_success "Formatting complete!"
}

cmd_type_check() {
    log_info "Running type checker..."
    mypy ${SRC_DIR} --ignore-missing-imports
    log_success "Type checking complete!"
}

cmd_security() {
    log_info "Running security scan..."
    bandit -r ${SRC_DIR} -c pyproject.toml -q
    log_success "Security scan complete!"
}

cmd_build() {
    log_info "Building packages..."

    # Clean first
    rm -rf build/ dist/ *.egg-info src/*.egg-info

    # Build
    python3 -m build

    log_success "Build complete! Packages in dist/"
    ls -la dist/
}

cmd_clean() {
    log_info "Cleaning artifacts..."

    # Python cache
    find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name '*.pyc' -delete 2>/dev/null || true
    find . -type f -name '*.pyo' -delete 2>/dev/null || true

    # Build artifacts
    rm -rf build/ dist/ *.egg-info src/*.egg-info

    # Test artifacts
    rm -rf .pytest_cache/ .coverage htmlcov/ .mypy_cache/ .ruff_cache/

    log_success "Clean complete!"
}

cmd_ci() {
    log_info "Running CI pipeline..."

    log_info "Step 1/5: Linting..."
    cmd_lint

    log_info "Step 2/5: Format check..."
    cmd_format --check

    log_info "Step 3/5: Type checking..."
    cmd_type_check

    log_info "Step 4/5: Security scan..."
    cmd_security

    log_info "Step 5/5: Running tests with coverage..."
    cmd_test coverage

    log_success "CI pipeline complete!"
}

cmd_release() {
    log_info "Preparing release..."

    # Run CI first
    cmd_ci

    # Build packages
    cmd_build

    log_success "Release preparation complete!"
    log_info "To publish, run: twine upload dist/*"
}

cmd_help() {
    echo -e "${BLUE}AcademicLint Build Script${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  install [dev|all]     Install dependencies"
    echo "  test [type]           Run tests (unit|integration|acceptance|performance|security|coverage)"
    echo "  lint [--fix]          Run linting"
    echo "  format [--check]      Format code"
    echo "  type-check            Run type checker"
    echo "  security              Run security scan"
    echo "  build                 Build packages"
    echo "  clean                 Clean artifacts"
    echo "  ci                    Run full CI pipeline"
    echo "  release               Prepare release"
    echo "  help                  Show this help"
}

# =============================================================================
# Main
# =============================================================================

check_python

case "${1:-help}" in
    install)
        cmd_install "$2"
        ;;
    test)
        cmd_test "$2"
        ;;
    lint)
        cmd_lint "$2"
        ;;
    format)
        cmd_format "$2"
        ;;
    type-check)
        cmd_type_check
        ;;
    security)
        cmd_security
        ;;
    build)
        cmd_build
        ;;
    clean)
        cmd_clean
        ;;
    ci)
        cmd_ci
        ;;
    release)
        cmd_release
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        log_error "Unknown command: $1"
        cmd_help
        exit 1
        ;;
esac
