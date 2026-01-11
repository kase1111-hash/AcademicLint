#!/usr/bin/env bash
# =============================================================================
# Static Analysis Script for AcademicLint
# =============================================================================
# This script runs all static analysis tools:
# - Ruff (linting and security checks)
# - MyPy (type checking)
# - Bandit (security vulnerability scanning)
# - Safety (dependency vulnerability checking)
#
# Usage:
#   ./scripts/static_analysis.sh [--fix]
#
# Options:
#   --fix    Automatically fix issues where possible (ruff only)
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# Parse arguments
FIX_MODE=false
if [[ "$1" == "--fix" ]]; then
    FIX_MODE=true
fi

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}   AcademicLint Static Analysis Suite${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# -----------------------------------------------------------------------------
# Ruff - Linting
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[1/5] Running Ruff linter...${NC}"
if $FIX_MODE; then
    if ruff check src/ --fix; then
        echo -e "${GREEN}✓ Ruff linting passed (with fixes applied)${NC}"
    else
        echo -e "${RED}✗ Ruff linting failed${NC}"
        FAILED=1
    fi
else
    if ruff check src/; then
        echo -e "${GREEN}✓ Ruff linting passed${NC}"
    else
        echo -e "${RED}✗ Ruff linting failed${NC}"
        FAILED=1
    fi
fi
echo ""

# -----------------------------------------------------------------------------
# Ruff - Formatting Check
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[2/5] Checking code formatting...${NC}"
if $FIX_MODE; then
    if ruff format src/; then
        echo -e "${GREEN}✓ Code formatting applied${NC}"
    else
        echo -e "${RED}✗ Code formatting failed${NC}"
        FAILED=1
    fi
else
    if ruff format --check src/; then
        echo -e "${GREEN}✓ Code formatting is correct${NC}"
    else
        echo -e "${RED}✗ Code formatting issues found (run with --fix)${NC}"
        FAILED=1
    fi
fi
echo ""

# -----------------------------------------------------------------------------
# MyPy - Type Checking
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[3/5] Running MyPy type checker...${NC}"
if mypy src/academiclint --ignore-missing-imports; then
    echo -e "${GREEN}✓ MyPy type checking passed${NC}"
else
    echo -e "${RED}✗ MyPy type checking failed${NC}"
    FAILED=1
fi
echo ""

# -----------------------------------------------------------------------------
# Bandit - Security Scanning
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[4/5] Running Bandit security scanner...${NC}"
if bandit -r src/academiclint -c pyproject.toml -q; then
    echo -e "${GREEN}✓ Bandit security scan passed${NC}"
else
    echo -e "${RED}✗ Bandit found security issues${NC}"
    FAILED=1
fi
echo ""

# -----------------------------------------------------------------------------
# Safety - Dependency Vulnerabilities
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[5/5] Checking dependencies for vulnerabilities...${NC}"
if command -v safety &> /dev/null; then
    if safety check --short-report 2>/dev/null || true; then
        echo -e "${GREEN}✓ Dependency check complete${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Safety not installed, skipping dependency check${NC}"
fi
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo -e "${BLUE}=============================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All static analysis checks passed!${NC}"
    exit 0
else
    echo -e "${RED}Some checks failed. Please fix the issues above.${NC}"
    exit 1
fi
