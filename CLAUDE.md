# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a GitHub Action that validates URL availability in repositories using the [urlsup](https://github.com/simeg/urlsup) Rust binary. The action has been modernized from a Docker-based approach to a composite action for significantly improved performance and user experience.

## Architecture (v2.0)

- **Composite Action**: Uses composite action architecture for 5-10x faster startup than Docker
- **Binary Caching**: Downloads and caches urlsup binary across workflow runs
- **Rich GitHub Integration**: Provides annotations, job summaries, and artifact reports
- **Structured Inputs**: 20+ inputs mapping directly to urlsup CLI options

## Key Components

- `action.yml` - Composite action definition with structured inputs and outputs
- `scripts/setup.sh` - Downloads and caches urlsup binary with version management
- `scripts/validate.sh` - Builds urlsup command and executes URL validation
- `scripts/annotate.sh` - Creates GitHub annotations for broken URLs
- `scripts/summary.sh` - Generates rich HTML job summaries
- `.github/workflows/example.yml` - Example workflow demonstrating usage

## Development Commands

### Testing the Action Locally
```bash
# Test setup script
./scripts/setup.sh

# Test validation with sample files
URLSUP_VERSION=latest INPUT_FILES="README.md" ./scripts/validate.sh

# Test annotation creation (requires GITHUB_WORKSPACE and mock report)
REPORT_PATH="test-report.json" ./scripts/annotate.sh

# Test summary generation
TOTAL_URLS=10 BROKEN_URLS=0 SUCCESS_RATE="100%" ./scripts/summary.sh
```

### Script Development
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Lint shell scripts (if shellcheck is available)
shellcheck scripts/*.sh

# Test individual components
bash -x scripts/setup.sh  # Debug mode
```

## Important Notes

### v2.0 Changes from v1.x
- **Breaking**: Removed Docker-based architecture
- **Breaking**: Replaced `args` input with structured inputs
- **New**: Binary caching for performance
- **New**: GitHub annotations and job summaries
- **New**: Rich outputs and artifact reports
- **Improved**: 5-10x faster startup time

### Action Requirements
- Requires `actions/checkout@v4` to access repository files
- Supports Linux, macOS, and Windows runners
- Downloads urlsup binary from GitHub releases
- Creates temporary files in `$GITHUB_WORKSPACE`

### Script Dependencies
- `curl` for downloading binaries
- `jq` (optional) for better JSON parsing
- Standard POSIX shell utilities
- GitHub Actions environment variables

### Testing Considerations
- Scripts use `$GITHUB_WORKSPACE` for file operations
- Requires GitHub Actions environment variables for full functionality
- Can be tested locally with mock environment variables
- Binary download requires internet connectivity

## File Structure
```
urlsup-action/
├── action.yml                  # Main composite action definition
├── README.md                   # User documentation with examples
├── CLAUDE.md                   # This development guide
├── scripts/
│   ├── setup.sh               # Binary download and caching
│   ├── validate.sh            # URL validation execution
│   ├── annotate.sh            # GitHub annotations creation
│   └── summary.sh             # Job summary generation
└── .github/workflows/
    └── example.yml            # Example usage workflow
```

## Version Management
- Uses semantic versioning (v2.0.0, v2.1.0, etc.)
- `urlsup-version` input allows specifying urlsup binary version
- Defaults to latest urlsup release
- Binary caching includes version verification