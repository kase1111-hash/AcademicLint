# =============================================================================
# AcademicLint Makefile
# =============================================================================
# Automated build, test, and deployment commands
#
# Usage:
#   make help          - Show available commands
#   make install       - Install dependencies
#   make test          - Run tests
#   make lint          - Run linting
#   make build         - Build package
#   make clean         - Clean build artifacts
# =============================================================================

.PHONY: help install install-dev install-all setup test test-cov test-unit \
        test-integration test-acceptance test-performance test-security \
        lint lint-fix format type-check security-scan static-analysis \
        build build-wheel build-sdist clean clean-pyc clean-build clean-test \
        docs serve-docs docker-build docker-run docker-test \
        version release pre-commit

# Default target
.DEFAULT_GOAL := help

# Project settings
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
PACKAGE := academiclint
SRC_DIR := src/$(PACKAGE)
TEST_DIR := tests

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "$(BLUE)AcademicLint - Build Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Usage:$(NC) make [target]"
	@echo ""
	@echo "$(YELLOW)Targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# Installation
# =============================================================================

install: ## Install production dependencies
	$(PIP) install -e .

install-dev: ## Install development dependencies
	$(PIP) install -e ".[dev]"

install-all: ## Install all dependencies (including optional)
	$(PIP) install -e ".[all]"

setup: install-dev ## Full development setup
	$(PYTHON) -m spacy download en_core_web_sm
	pre-commit install
	@echo "$(GREEN)Development environment ready!$(NC)"

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	$(PYTEST) $(TEST_DIR) -v

test-cov: ## Run tests with coverage report
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	$(PYTEST) $(TEST_DIR) -v -m "not integration and not acceptance and not performance and not security" \
		--ignore=$(TEST_DIR)/test_integration_linter.py \
		--ignore=$(TEST_DIR)/test_integration_api.py \
		--ignore=$(TEST_DIR)/test_acceptance.py \
		--ignore=$(TEST_DIR)/test_performance.py \
		--ignore=$(TEST_DIR)/test_security.py

test-integration: ## Run integration tests only
	$(PYTEST) $(TEST_DIR)/test_integration_*.py -v

test-acceptance: ## Run acceptance tests only
	$(PYTEST) $(TEST_DIR)/test_acceptance.py -v

test-performance: ## Run performance tests only
	$(PYTEST) $(TEST_DIR)/test_performance.py -v --timeout=300

test-security: ## Run security tests only
	$(PYTEST) $(TEST_DIR)/test_security.py -v

test-regression: ## Run regression tests only
	$(PYTEST) $(TEST_DIR)/test_regression.py -v

test-quick: ## Run quick smoke tests
	$(PYTEST) $(TEST_DIR) -v -x --timeout=60 -q

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linter (ruff)
	ruff check $(SRC_DIR)
	ruff check $(TEST_DIR)

lint-fix: ## Run linter and fix issues
	ruff check $(SRC_DIR) --fix
	ruff check $(TEST_DIR) --fix

format: ## Format code (ruff format)
	ruff format $(SRC_DIR)
	ruff format $(TEST_DIR)

format-check: ## Check code formatting
	ruff format --check $(SRC_DIR)
	ruff format --check $(TEST_DIR)

type-check: ## Run type checker (mypy)
	mypy $(SRC_DIR) --ignore-missing-imports

security-scan: ## Run security scanner (bandit)
	bandit -r $(SRC_DIR) -c pyproject.toml -q

static-analysis: lint format-check type-check security-scan ## Run all static analysis

# =============================================================================
# Building
# =============================================================================

build: clean-build build-wheel build-sdist ## Build distribution packages
	@echo "$(GREEN)Build complete! Packages in dist/$(NC)"

build-wheel: ## Build wheel package
	$(PYTHON) -m build --wheel

build-sdist: ## Build source distribution
	$(PYTHON) -m build --sdist

# =============================================================================
# Cleaning
# =============================================================================

clean: clean-pyc clean-build clean-test ## Clean all artifacts

clean-pyc: ## Remove Python cache files
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	find . -type f -name '*.pyo' -delete 2>/dev/null || true
	find . -type f -name '*~' -delete 2>/dev/null || true

clean-build: ## Remove build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info

clean-test: ## Remove test artifacts
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

# =============================================================================
# Documentation
# =============================================================================

docs: ## Build documentation
	@echo "$(YELLOW)Documentation build not configured yet$(NC)"

serve-docs: ## Serve documentation locally
	@echo "$(YELLOW)Documentation server not configured yet$(NC)"

# =============================================================================
# Docker
# =============================================================================

docker-build: ## Build Docker image
	docker build -t $(PACKAGE):latest .

docker-run: ## Run Docker container
	docker run -it --rm $(PACKAGE):latest

docker-test: ## Run tests in Docker
	docker-compose run --rm test

docker-dev: ## Start development environment in Docker
	docker-compose up -d dev

# =============================================================================
# Release
# =============================================================================

version: ## Show current version
	@$(PYTHON) -c "from $(PACKAGE) import __version__; print(__version__)"

release-patch: ## Bump patch version (0.0.X)
	@echo "$(YELLOW)Version bumping requires manual update in pyproject.toml$(NC)"

release-minor: ## Bump minor version (0.X.0)
	@echo "$(YELLOW)Version bumping requires manual update in pyproject.toml$(NC)"

release-major: ## Bump major version (X.0.0)
	@echo "$(YELLOW)Version bumping requires manual update in pyproject.toml$(NC)"

# =============================================================================
# Pre-commit
# =============================================================================

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-update: ## Update pre-commit hooks
	pre-commit autoupdate

# =============================================================================
# Development Utilities
# =============================================================================

check: lint type-check test ## Run all checks (lint, type, test)

ci: static-analysis test-cov ## Run CI pipeline locally

dev-server: ## Start development API server
	uvicorn $(PACKAGE).api.app:app --reload --host 0.0.0.0 --port 8080

repl: ## Start Python REPL with package loaded
	$(PYTHON) -c "from $(PACKAGE) import *; import code; code.interact(local=locals())"
