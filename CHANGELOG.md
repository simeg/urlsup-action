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
- Binary caching with `actions/cache@v4` for urlsup installation in CI workflows
- Rich GitHub annotations for broken URLs with actionable suggestions
- Detailed HTML job summaries
- Artifact upload for JSON reports
- 20+ structured inputs mapping to urlsup CLI options
- Comprehensive input validation
- Better error messages and debugging output with step-by-step troubleshooting
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
- Smart URL fix suggestions based on error types and patterns
- Context-aware troubleshooting for GitHub URLs, localhost, SSL issues, and timeouts
- Comprehensive FAQ section with real-world debugging scenarios
- JSON report caching for improved performance when processing large result sets
- Batch annotation processing for better performance with many broken URLs
- Optimized file I/O operations for GitHub Actions outputs
- Anonymous telemetry collection for performance insights and optimization
- GitHub Actions performance metrics in job summaries and annotations
- Repository size categorization for performance insights
- Setup timing and cache hit tracking
- Experimental parallel file processing for large repositories with `parallel-processing` input
- Intelligent file discovery and batching for optimized parallel processing performance
- Automatic parallel processing enablement based on repository size (20+ files threshold)
- Report merging functionality to combine results from parallel processing batches

### Changed
- **BREAKING**: Scripts migrated from Bash to Python for improved maintainability
- **BREAKING**: Replaced Docker-based architecture with composite action
- **BREAKING**: Replaced `args` input with structured inputs
- Default timeout reduced from 10s to 5s
- Now requires `actions/checkout@v4`
- Enhanced command building logic with better input validation
- Improved JSON parsing with fallback for non-JSON output
- Better handling of urlsup version management and caching
- Enhanced annotation creation with multiple format support and actionable suggestions
- Improved summary generation with expandable details section
- Improved error handling in Python scripts with detailed troubleshooting guides
- Enhanced documentation structure with practical debugging examples
- README reorganized for better flow (moved Migration and GitHub Integration sections)
- Internal Scripts documentation updated to reflect Python implementation
- Makefile targets standardized and aligned for consistency
- Linting configuration updated to handle test file import patterns
- Security dependencies updated (setuptools ≥78.1.1, urllib3 ≥2.5.0)
- FAQ section enhanced with real-world troubleshooting scenarios and solutions
- Annotation messages now include emoji indicators and context-specific fix suggestions
- Performance optimizations for report processing and file operations

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