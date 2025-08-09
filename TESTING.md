# Testing Guide

This document describes the testing infrastructure for urlsup-action, including how to run tests locally and in CI.

## 🧪 Test Structure

### Test Categories

1. **Unit Tests** (`tests/test_*.py`) - Test individual functions and modules
2. **End-to-End Tests** (`tests/e2e/`) - Test the complete action workflow
3. **Integration Tests** - Test action with real urlsup binary
4. **Syntax Validation** - Validate example workflows and configurations

### Test Files

```
tests/
├── __init__.py
├── test_validate.py       # Tests for validate.py script
├── test_annotate.py       # Tests for annotate.py script
├── test_summary.py        # Tests for summary.py script
├── run_tests.py           # Test runner (fallback)
└── e2e/
    ├── __init__.py
    ├── generate_test_links.py    # Test data generator
    └── test_e2e_action.py        # End-to-end tests
```

## 🚀 Running Tests

### Prerequisites

First, install Poetry if you haven't already:

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Or visit: https://python-poetry.org/docs/#installation
```

Then install development dependencies:

```bash
# Install development dependencies with Poetry
poetry install --with dev,ci

# Or use make
make install

# Or install manually with cargo
cargo install urlsup
```

### Local Testing

**Run all tests:**
```bash
# Using Poetry + pytest (recommended)
poetry run pytest tests/ -v

# Using make (uses Poetry)
make test

# Using test runner (tries Poetry, then fallback)
python tests/run_tests.py
```

**Run specific test categories:**
```bash
# Unit tests only
make test-unit
poetry run pytest tests/ -k "not e2e"

# End-to-end tests only
make test-e2e
poetry run pytest tests/e2e/ -v

# Tests with coverage
make test-cov
poetry run pytest tests/ --cov=scripts --cov-report=html
```

**Run specific test files:**
```bash
# Test specific script
poetry run pytest tests/test_validate.py -v

# Test specific function
poetry run pytest tests/test_validate.py::TestBuildCommand::test_default_command -v
```

### Development Workflow

**Quick development check:**
```bash
make dev-check
# Runs: format → lint → unit tests
```

**Full local CI simulation:**
```bash
make ci-local
# Runs: lint → test → security
```

**Code formatting:**
```bash
make format
# Runs: black + isort
```

## 🌐 CI Pipeline

### GitHub Actions Workflows

1. **CI (`ci.yml`)** - Main testing pipeline
2. **Tests (`tests.yml`)** - Coverage and status reporting

### CI Jobs

1. **test-python-scripts** - Unit tests across OS/Python matrix
2. **test-action-integration** - Real action testing with urlsup binary
3. **test-script-execution** - Script functionality across platforms
4. **test-examples-syntax** - Validate example workflows/configs
5. **test-action-metadata** - Validate action.yml structure
6. **test-documentation** - Check documentation completeness
7. **lint-and-format** - Code quality checks
8. **security-scan** - Security vulnerability scanning

## 📊 Test Data Generation

### Generating Test Repositories

```bash
# Generate test data for E2E tests
make test-data
cd tests/e2e && python generate_test_links.py
```

This creates a test repository structure:
```
test-links-dir/
├── dir-one/
│   ├── working-urls.md      # URLs that should work
│   ├── broken-urls.md       # URLs that should fail
│   └── dir-two/
│       └── mixed-urls.md    # Mix of working/broken URLs
├── config-test.md           # Configuration testing scenarios
├── urls.txt                 # Plain text URLs
├── documentation.rst        # reStructuredText format
└── page.html                # HTML format
```

### Test Scenarios

- **Working URLs:** GitHub, Example.com, Google
- **Broken URLs:** Non-existent domains, invalid TLDs, unreachable ports
- **Edge Cases:** Redirects, slow responses, rate limiting
- **Local URLs:** Localhost, 127.0.0.1 (should be filtered)

## 🐛 Debugging Tests

### Verbose Output

```bash
# Maximum verbosity
poetry run pytest tests/ -vvv

# Show local variables in tracebacks
poetry run pytest tests/ --tb=long

# Stop on first failure
poetry run pytest tests/ -x

# Debug specific test
poetry run pytest tests/test_validate.py::TestBuildCommand::test_files_input -vvv -s
```

### Test Debugging Tips

1. **Use `print()` statements** in tests for debugging
2. **Add `-s` flag** to see print output: `pytest -s`
3. **Use `--pdb`** to drop into debugger on failure
4. **Check test data** in `tests/e2e/test-links-dir/`
5. **Verify environment variables** are set correctly

### Common Issues

**Import errors:**
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=$PWD:$PYTHONPATH
poetry run pytest tests/
```

**Missing test data:**
```bash
# Regenerate test data
python tests/e2e/generate_test_links.py
```

## 📈 Coverage Reporting

### Local Coverage

```bash
# Generate coverage report
poetry run pytest tests/ --cov=scripts --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🔒 Security Testing

### Security Scans

```bash
# Run security checks
make security

# Individual tools
poetry run bandit -r scripts/           # Security linting
poetry run safety check                 # Dependency vulnerability check
```

### Security Test Categories

1. **Code Security** - Bandit scans for common security issues
2. **Dependency Security** - Safety checks for known vulnerabilities
3. **Input Validation** - Tests for proper input sanitization
4. **Environment Security** - Tests for secure environment handling

## 🧩 Test Organization Best Practices

### Writing New Tests

1. **Follow naming convention:** `test_*.py` files, `test_*` functions
2. **Use descriptive names:** `test_build_command_with_timeout_setting`
3. **Group related tests:** Use test classes for related functionality
4. **Add docstrings:** Explain what the test verifies
5. **Use markers:** Mark tests as unit/integration/e2e/slow/network

### Test Structure

```python
class TestValidateScript:
    """Tests for validate.py functionality."""

    def test_to_bool_true_values(self):
        """Test that various true values convert correctly."""
        for value in ["true", "True", "1", "yes"]:
            assert to_bool(value) is True

    @pytest.mark.slow
    def test_real_url_validation(self):
        """Test validation with real URLs (slow test)."""
        # Test implementation
```

### Mock Usage

```python
# Mock external dependencies
@patch('subprocess.run')
def test_urlsup_execution(self, mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    # Test implementation

# Mock environment variables
@patch.dict(os.environ, {'INPUT_TIMEOUT': '30'}, clear=True)
def test_timeout_setting(self):
    # Test implementation
```

## 🔄 Continuous Integration

### Local CI Simulation

Before pushing changes, run the full CI pipeline locally:

```bash
# Quick check
make dev-check

# Full CI simulation
make ci-local

# Check specific aspects
make lint
make test
make security
make validate-examples
```

### CI Performance

- **Caching:** Dependencies and build artifacts are cached
- **Selective running:** Only relevant tests run based on file changes
- **Fast feedback:** Critical tests run first

## 📚 Additional Resources

- **Poetry documentation:** https://github.com/python-poetry/poetry
- **Coverage.py documentation:** https://coverage.readthedocs.io/
- **GitHub Actions testing:** https://docs.github.com/en/actions
- **Python testing best practices:** https://docs.python-guide.org/writing/tests/
