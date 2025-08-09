# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-08-09

### Added
- **BREAKING**: Migrated from shell scripts to Python scripts for better reliability and testing
- Rich metadata outputs: `total-files`, `processed-files`, `total-found-urls`, `unique-urls`, `status`
- Enhanced job summaries with file processing statistics
- Better error handling and logging with colored output
- Structured input validation and type conversion
- Support for `failure-threshold` input parameter
- Configuration file support (`config` and `no-config` inputs)
- Enhanced progress bar visualization in job summaries
- Duplicate URL detection and reporting
- Unit tests for Python scripts in `scripts/` directory
- End-to-end tests with generated test repositories
- Test runner script for automated testing
- Example workflows directory with real-world use cases (13+ examples)
- Configuration templates for common scenarios (5 pre-built configs)
- Composite action architecture (5-10x faster than Docker)
- Binary caching with `actions/cache@v4`
- Rich GitHub annotations for broken URLs
- Detailed HTML job summaries
- Artifact upload for JSON reports
- 20+ structured inputs mapping to urlsup CLI options
- Comprehensive input validation
- Better error messages and debugging output
- Progress bar support (disabled in CI)
- Enhanced GitHub integration
- Poetry-based dependency management with `pyproject.toml`
- Comprehensive development environment with Makefile
- Code quality tools: black, isort, flake8, pydocstyle
- Security scanning with bandit and safety
- Test coverage reporting with pytest-cov
- CI/CD pipeline with GitHub Actions
- YAML and JSON validation for examples
- Development documentation in `TESTING.md`
- `no-progress` input for disabling progress bars
- Shared utilities in `scripts/common.py` for consistent functionality
- Support for multiple urlsup output formats (backward compatibility)
- Enhanced markdown escaping for job summaries
- Centralized logging system with color support

### Changed
- **BREAKING**: Scripts migrated from Bash to Python for improved maintainability
- **BREAKING**: Replaced Docker-based architecture with composite action
- **BREAKING**: Replaced `args` input with structured inputs
- Default timeout reduced from 10s to 5s
- Now requires `actions/checkout@v4`
- Enhanced command building logic with better input validation
- Improved JSON parsing with fallback for non-JSON output
- Better handling of urlsup version management and caching
- Enhanced annotation creation with multiple format support
- Improved summary generation with expandable details section
- Improved error handling in Python scripts
- Enhanced documentation structure
- README reorganized for better flow (moved Migration and GitHub Integration sections)
- Internal Scripts documentation updated to reflect Python implementation
- Makefile targets standardized and aligned for consistency
- Linting configuration updated to handle test file import patterns
- Security dependencies updated (setuptools ≥78.1.1, urllib3 ≥2.5.0)

### Fixed
- Version comparison logic in setup script
- Error handling for malformed JSON reports
- File path cleaning in annotations
- Timeout handling in binary execution
- YAML scanner errors in example workflows (escaped regex patterns)
- Unused import violations in scripts and test files
- Code formatting and line length issues
- Import ordering in test files
- Whitespace and trailing space issues throughout codebase
- Flake8 and pydocstyle configuration for Python project structure
- E402 import errors in test files with sys.path modifications
- Long string formatting for better readability

### Removed
- Legacy shell script implementations
