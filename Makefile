# Makefile for urlsup-action development

.PHONY: help install test test-unit test-e2e lint lint-docstrings format clean dev-setup ci ci-local poetry-check

# Default target
help:
	@echo "🔧 urlsup-action Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install development dependencies with Poetry"
	@echo "  make dev-setup        Full development environment setup"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run only unit tests"
	@echo "  make test-e2e         Run only end-to-end tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linting checks"
	@echo "  make lint-docstrings  Run linting checks on docstrings only"
	@echo "  make format           Format code with black and isort"
	@echo "  make security         Run security checks"
	@echo "  make validate-examples  Validate YAML and JSON example files"
	@echo ""
	@echo "CI/Development:"
	@echo "  make ci               Run linter, tests, and validate-examples"
	@echo "  make ci-local         Run full CI pipeline locally"
	@echo "  make clean            Clean up generated files"
	@echo ""
	@echo "Dependencies:"
	@echo "  make poetry-check     Check if Poetry is installed"

# Check if Poetry is installed
poetry-check:
	@command -v poetry >/dev/null 2>&1 || { \
		echo "❌ Poetry is not installed!"; \
		echo ""; \
		echo "Please install Poetry first:"; \
		echo "  curl -sSL https://install.python-poetry.org | python3 -"; \
		echo "  or visit: https://python-poetry.org/docs/#installation"; \
		echo ""; \
		exit 1; \
	}
	@echo "✅ Poetry is installed: $$(poetry --version)"

# Install development dependencies
install: poetry-check
	@echo "📦 Installing development dependencies with Poetry..."
	poetry install --with dev,ci
	@echo "✅ Dependencies installed!"

# Full development setup
dev-setup: install
	@echo "🔧 Setting up development environment..."
	@echo ""
	@echo "📋 For end-to-end tests, you'll also need urlsup installed:"
	@echo "  cargo install urlsup"
	@echo ""
	@echo "If you don't have Rust/Cargo, install it first:"
	@echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
	@echo "  source ~/.cargo/env"
	@echo "  cargo install urlsup"
	@echo ""
	@echo "✅ Development environment ready!"
	@echo "Run 'make test' to verify everything works."

# Run all tests
test: poetry-check
	@echo "🧪 Running all tests..."
	poetry run pytest tests/ -v

# Run only unit tests
test-unit: poetry-check
	@echo "🧪 Running unit tests..."
	poetry run pytest tests/ -v -k "not e2e"

# Run only end-to-end tests  
test-e2e: poetry-check
	@echo "🧪 Running end-to-end tests..."
	poetry run pytest tests/e2e/ -v

# Run tests with coverage
test-cov: poetry-check
	@echo "🧪 Running tests with coverage..."
	poetry run pytest tests/ -v --cov=scripts --cov-report=term --cov-report=html

# CI test pipeline
ci: lint validate-examples test
	@echo "🧪 Running CI tests with coverage..."
	poetry run pytest tests/ --cov=scripts --cov-report=xml --cov-report=term

# Lint code
lint: poetry-check
	@echo "🔍 Running linting checks..."
	@echo "Checking formatting with black..."
	poetry run black --check scripts/ tests/
	@echo "Checking import sorting with isort..."
	poetry run isort --check-only scripts/ tests/
	@echo "Linting with flake8..."
	poetry run flake8 scripts/ tests/ --max-line-length=100 --ignore=E203,W503,E402
	@echo "Checking docstrings..."
	poetry run pydocstyle scripts/ --ignore=D100,D101,D102,D103,D104,D105,D107,D200,D203,D212,D401,D213
	@echo "✅ All linting checks passed!"

# Lint docstrings only
lint-docstrings: poetry-check
	@echo "🔍 Checking docstrings..."
	poetry run pydocstyle scripts/ --ignore=D100,D101,D102,D103,D104,D105,D107,D203,D211,D213
	@echo "✅ Docstring checks passed!"

# Remove trailing whitespace
fix-whitespace:
	@echo "🧹 Removing trailing whitespace from all text files..."
	find . -name "*.md" -exec sed -i '' 's/[[:space:]]*$$//' {} \;
	find . -name "*.yml" -exec sed -i '' 's/[[:space:]]*$$//' {} \;
	find . -name "*.yaml" -exec sed -i '' 's/[[:space:]]*$$//' {} \;
	find . -name "*.json" -exec sed -i '' 's/[[:space:]]*$$//' {} \;
	find . -name "*.txt" -exec sed -i '' 's/[[:space:]]*$$//' {} \;
	@echo "✅ Trailing whitespace removed!"

# Format code
format: poetry-check
	@echo "🎨 Formatting code..."
	poetry run black scripts/ tests/
	poetry run isort scripts/ tests/
	@echo "🧹 Removing trailing whitespace from .md and .yml files..."
	find . -name "*.md" -exec sed -i '' 's/[[:space:]]*$$//' {} \;
	find . -name "*.yml" -exec sed -i '' 's/[[:space:]]*$$//' {} \;
	@echo "✅ Code formatted!"

# Security checks
security: poetry-check
	@echo "🔒 Running security checks..."
	poetry run bandit -r scripts/ --severity-level medium
	poetry run safety check
	@echo "✅ Security checks completed!"

# Run full CI pipeline locally
ci-local: lint test security
	@echo "🎉 Local CI pipeline completed successfully!"

# Generate test data
test-data: poetry-check
	@echo "📊 Generating test data..."
	cd tests/e2e && poetry run python generate_test_links.py
	@echo "✅ Test data generated!"

# Clean up generated files
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	find . -name "coverage.xml" -delete 2>/dev/null || true
	rm -rf tests/e2e/test-links-dir/ 2>/dev/null || true
	@echo "✅ Cleanup completed!"

# Validate examples
validate-examples: poetry-check
	@echo "📋 Validating example workflows..."
	@for file in examples/workflows/*.yml; do \
		echo "Checking $$file..."; \
		poetry run python -c "import yaml; yaml.safe_load(open('$$file'))" || exit 1; \
	done
	@echo "📋 Validating configuration files..."
	@for file in examples/configs/*.json; do \
		echo "Checking $$file..."; \
		poetry run python -c "import json; json.load(open('$$file'))" || exit 1; \
	done
	@echo "✅ All examples are valid!"

# Quick development check
dev-check: format lint test-unit
	@echo "🚀 Quick development check completed!"
