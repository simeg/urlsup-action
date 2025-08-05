# urlsup-action

**Fast, concurrent URL validation for your repositories** 🚀

GitHub Action that validates URL availability in your files using the powerful [urlsup](https://github.com/simeg/urlsup) Rust binary. Perfect for catching broken links in documentation, ensuring all URLs return successful HTTP status codes.

## ✨ Features

- **⚡ Lightning Fast**: Composite action with binary caching (5-10x faster than Docker)
- **🔄 Concurrent**: Multi-threaded URL checking with configurable concurrency
- **🎯 Smart Filtering**: Allowlists, status code filtering, and regex exclusions
- **📊 Rich Reports**: GitHub annotations, job summaries, and detailed JSON reports
- **🔧 Highly Configurable**: 20+ inputs mapping to all urlsup features
- **📱 Cross-Platform**: Supports Linux, macOS, and Windows runners
- **💾 Efficient Caching**: Binary caching across workflow runs

## 🚀 Quick Start

```yaml
name: Check URLs

on:
  push:
  pull_request:
  schedule:
    - cron: '0 9 * * 1'  # Weekly on Monday

jobs:
  url-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate URLs
        uses: simeg/urlsup-action@v2
        with:
          files: '**/*.md'
          timeout: 5
          retry: 2
```

## 📋 Inputs

### File Selection
| Input | Description | Default |
|-------|-------------|---------|
| `files` | Files or directories to check (space-separated) | `'.'` |
| `recursive` | Recursively process directories | `true` |
| `include-extensions` | File extensions to process (comma-separated) | `'md,rst,txt,html'` |

### Network Configuration
| Input | Description | Default   |
|-------|-------------|-----------|
| `timeout` | Connection timeout in seconds | `5`       |
| `concurrency` | Number of concurrent requests | CPU cores |
| `retry` | Retry attempts for failed requests | `2`       |
| `retry-delay` | Delay between retries in milliseconds | `1000`    |
| `rate-limit` | Delay between requests in milliseconds | `100`     |

### URL Filtering
| Input | Description | Default |
|-------|-------------|---------|
| `allowlist` | URLs to allow (comma-separated patterns) | |
| `allow-status` | HTTP status codes to allow (comma-separated) | `'200,202,204'` |
| `exclude-pattern` | URL patterns to exclude (regex) | |
| `allow-timeout` | Allow URLs that timeout | `false` |

### Output Configuration
| Input | Description | Default |
|-------|-------------|---------|
| `quiet` | Suppress progress output | `false` |
| `verbose` | Enable verbose logging | `false` |

### Advanced Options
| Input | Description | Default |
|-------|-------------|---------|
| `user-agent` | Custom User-Agent header | `'urlsup-action/2.2.0'` |
| `proxy` | HTTP/HTTPS proxy URL | |
| `insecure` | Skip SSL certificate verification | `false` |

### Action-Specific Options
| Input | Description | Default |
|-------|-------------|---------|
| `urlsup-version` | Version of urlsup to use | `'latest'` |
| `create-annotations` | Create GitHub annotations for broken URLs | `true` |
| `fail-on-error` | Fail the action if broken URLs are found | `true` |

## 📤 Outputs

| Output | Description |
|--------|-------------|
| `total-urls` | Total number of URLs checked |
| `broken-urls` | Number of broken URLs found |
| `success-rate` | Percentage of working URLs |
| `report-path` | Path to detailed JSON report |
| `exit-code` | Exit code from urlsup (0 = success) |

## 📖 Usage Examples

### Basic URL Checking
```yaml
- name: Check all markdown files
  uses: simeg/urlsup-action@v2
  with:
    files: '**/*.md'
    include-extensions: 'md'
```

### Advanced Configuration
```yaml
- name: Check URLs with custom settings
  uses: simeg/urlsup-action@v2
  with:
    files: 'docs/ README.md CHANGELOG.md'
    timeout: 15
    retry: 3
    concurrency: 20
    allow-status: '200,202,204,404'
    exclude-pattern: 'localhost|127\.0\.0\.1|example\.com'
    allowlist: 'github.com,docs.github.com'
    user-agent: 'MyBot/1.0'
```

### Non-Blocking URL Check
```yaml
- name: Check URLs (non-blocking)
  uses: simeg/urlsup-action@v2
  with:
    files: 'docs/'
    fail-on-error: false
    create-annotations: true
```

### Complete Workflow with Manual Trigger
```yaml
name: URL Validation

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 9 * * 1'  # Weekly
  workflow_dispatch:
    inputs:
      files:
        description: 'Files to check'
        default: '**/*.md'
      strict:
        description: 'Strict mode (fail on any broken URL)'
        type: boolean
        default: true

permissions:
  contents: read

jobs:
  validate-urls:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Validate URLs
        uses: simeg/urlsup-action@v2
        with:
          files: ${{ inputs.files || '**/*.md' }}
          timeout: 5
          retry: 2
          rate-limit: 100
          allow-status: ${{ inputs.strict && '200' || '200,202,204' }}
          fail-on-error: ${{ inputs.strict || true }}

      - name: Comment on PR
        if: github.event_name == 'pull_request' && failure()
        uses: actions/github-script@v7
        with:
          script: |
            const { data: comments } = await github.rest.issues.listComments({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
            });

            const botComment = comments.find(comment =>
              comment.user.type === 'Bot' && comment.body.includes('URL validation failed')
            );

            const body = '🔗 **URL validation failed** - Some links in your changes are broken. Please check the workflow run for details.';

            if (botComment) {
              await github.rest.issues.updateComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: botComment.id,
                body
              });
            } else {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body
              });
            }
```

## 🔧 Migration from v1

**v1 (Docker-based):**
```yaml
- uses: simeg/urlsup-action@v1
  with:
    args: '*.md --threads 10 --allow 429'
```

**v2 (Composite, faster):**
```yaml
- uses: simeg/urlsup-action@v2
  with:
    files: '*.md'
    concurrency: 10
    allow-status: '200,429'
```

### Breaking Changes
- `args` input removed → Use structured inputs
- Default timeout changed from 10s → 5s
- Now creates annotations by default
- Requires `actions/checkout@v4`

## 🎯 GitHub Integration

### Annotations
Broken URLs appear as inline annotations in your files:
```
❌ example.md:15 Broken URL: https://example.com/dead-link (HTTP 404)
```

### Job Summaries
Rich HTML summaries with:
- 📊 Success rate visualization
- 📋 Broken URL details table
- 💡 Actionable recommendations
- 📁 Downloadable JSON reports

### Artifacts
Detailed JSON reports are uploaded as workflow artifacts containing:
- Complete URL validation results
- File locations and line numbers
- HTTP status codes and error messages
- Timing and performance metrics

## ⚠️ Common Use Cases

### Documentation Sites
```yaml
- uses: simeg/urlsup-action@v2
  with:
    files: 'docs/ *.md'
    include-extensions: 'md,rst'
    allow-status: '200,202'
    exclude-pattern: 'localhost|127\.0\.0\.1'
```

### API Documentation
```yaml
- uses: simeg/urlsup-action@v2
  with:
    files: 'api-docs/'
    timeout: 60
    retry: 3
    allowlist: 'api.example.com,docs.example.com'
```

### Lenient Checking
```yaml
- uses: simeg/urlsup-action@v2
  with:
    allow-status: '200,202,204,301,302,429'
    allow-timeout: true
    fail-on-error: false
```

## 🔧 Internal Scripts

The action uses several internal scripts located in the `scripts/` directory:

### **scripts/setup.sh**
Downloads and caches the urlsup binary for fast execution across workflow runs.

**Key features:**
- Downloads urlsup via `cargo install` if not cached
- Caches binary in `~/.cache/urlsup` with version verification
- Adds binary to PATH for subsequent workflow steps
- Handles Rust toolchain installation if needed

### **scripts/validate.sh**
Builds the urlsup command with all input parameters and executes URL validation.

**Key features:**
- Translates GitHub Action inputs to urlsup CLI arguments
- Executes urlsup with proper stdout/stderr handling
- Parses JSON output to extract metrics (total URLs, broken URLs, success rate)
- Sets GitHub Action outputs for use in subsequent steps

### **scripts/annotate.sh**
Creates GitHub annotations for broken URLs found during validation.

**Key features:**
- Parses urlsup JSON output to identify broken URLs
- Creates inline file annotations showing broken URLs with line numbers
- Handles both jq-based and fallback parsing methods
- Formats error messages with HTTP status codes and error details

### **scripts/summary.sh**
Generates rich HTML job summaries for the GitHub Actions interface.

**Key features:**
- Creates formatted job summary with success metrics
- Displays progress bar visualization of success rate
- Lists detailed broken URL information in table format
- Provides actionable recommendations for fixing issues
- Includes expandable details section with action metadata

These scripts work together to provide a seamless URL validation experience with rich GitHub integration, performance optimization through caching, and comprehensive error reporting.

## 🧪 Testing & Development

This action includes comprehensive testing infrastructure:

- **Unit Tests** - Full coverage of Python scripts with pytest
- **End-to-End Tests** - Real-world validation scenarios with generated test data
- **CI Pipeline** - Multi-platform testing across Python versions
- **Example Workflows** - Real-world configurations in `examples/`
- **Configuration Templates** - Pre-built configs for common scenarios

### For Contributors

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install development dependencies
make install

# Run tests
make test

# Check code quality
make lint

# Format code
make format

# Run full CI simulation
make ci-local
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## 📚 Documentation & Examples

- **[Examples Directory](examples/)** - Real-world workflow examples and configurations
- **[Configuration Guide](examples/configs/)** - Pre-built configuration templates
- **[Changelog](CHANGELOG.md)** - Version history and migration guides
- **[Testing Guide](TESTING.md)** - Testing infrastructure and contribution guidelines

## 🔗 Related

- **[urlsup](https://github.com/simeg/urlsup)** - The underlying Rust CLI tool
- **[Actions Marketplace](https://github.com/marketplace/actions/url-validator)** - Find this action
- **[GitHub Actions Documentation](https://docs.github.com/en/actions)** - Learn more about workflows

## 📄 License

MIT © [Simon Egersand](https://github.com/simeg)
[REMOVE ME](https://github.com/simeg23849u923)
