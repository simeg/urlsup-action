# urlsup-action

**Fast, concurrent URL validation for your repositories** 🚀

GitHub Action that validates URL availability in your files using the powerful [urlsup](https://github.com/simeg/urlsup) Rust binary. Perfect for catching broken links in documentation, ensuring all URLs return successful HTTP status codes.

**There's plenty of examples in the [examples/](examples/) directory, including real-world configurations and pre-built templates that you can use to quickly set up URL validation in your workflows.**

<img src="banner.png" alt="Dotfiles Banner" width="100%" style="display: block; margin: 0 auto;">

## 📑 Table of Contents

- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [📋 Inputs](#-inputs)
- [📤 Outputs](#-outputs)
- [📖 Usage Examples](#-usage-examples)
- [⚠️ Common Use Cases](#-common-use-cases)
- [❓ FAQ](#-faq)
- [📚 Documentation & Examples](#-documentation--examples)
- [🔧 Migration from v1](#-migration-from-v1)
- [🎯 GitHub Integration](#-github-integration)
- [🔧 Internal Scripts](#-internal-scripts)
- [🧪 Testing & Development](#-testing--development)
- [🔗 Related](#-related)
- [📄 License](#-license)

---

## ✨ Features

- **⚡ Lightning Fast**: Composite action with binary caching (5-10x faster than Docker)
- **🔄 Concurrent**: Multi-threaded URL checking with configurable concurrency
- **🎯 Smart Filtering**: Allowlists, status code filtering, and regex exclusions
- **📊 Rich Reports**: GitHub annotations, job summaries, and detailed JSON reports
- **🔧 Highly Configurable**: 20+ inputs mapping to all urlsup features

## 🚀 Quick Start

```yaml
name: Validate URLs are up

on:
  push:
  pull_request:
  schedule:
    - cron: '0 9 * * 1'  # Weekly on Monday

jobs:
  url-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate URLs
        id: validate-urls
        uses: simeg/urlsup-action@v2
        with:
          files: '.'
          recursive: true
          timeout-seconds: 5
          retry: 2
```

> **💡 Performance Note**: The action automatically caches the urlsup binary for lightning-fast subsequent runs (5-10x speedup after first execution).

## 📋 Inputs

### File Selection
| Input                | Description                                     | Default             |
|----------------------|-------------------------------------------------|---------------------|
| `files`              | Files or directories to check (space-separated) | `'.'`               |
| `recursive`          | Recursively process directories                 | `true`              |
| `include-extensions` | File extensions to process (comma-separated)    | `'md,rst,txt,html'` |

### Network Configuration
| Input             | Description                            | Default     |
|-------------------|----------------------------------------|-------------|
| `timeout-seconds` | Connection timeout in seconds          | `5`         |
| `concurrency`     | Number of concurrent requests          | # CPU cores |
| `retry`           | Retry attempts for failed requests     | `2`         |
| `retry-delay-ms`  | Delay between retries in milliseconds  | `1000`      |
| `rate-limit-ms`   | Delay between requests in milliseconds | `100`       |

### URL Filtering
| Input               | Description                                                                                            | Default         |
|---------------------|--------------------------------------------------------------------------------------------------------|-----------------|
| `allowlist`         | URLs to allow (comma-separated patterns)                                                               |                 |
| `allow-status`      | HTTP status codes to allow (comma-separated)                                                           | `'200,202,204'` |
| `exclude-pattern`   | URL patterns to exclude (regex)                                                                        |                 |
| `allow-timeout`     | Allow URLs that timeout                                                                                | `false`         |
| `failure-threshold` | Fail only if more than X% of URLs are broken (0-100). Leave empty to fail on any broken URL (default). | `''`            |

### Output Configuration
| Input     | Description                                        | Default  |
|-----------|----------------------------------------------------|----------|
| `quiet`   | Suppress progress output                           | `false`  |
| `verbose` | Enable verbose logging                             | `false`  |

### Advanced Options
| Input        | Description                       | Default                            |
|--------------|-----------------------------------|------------------------------------|
| `user-agent` | Custom User-Agent header          | `'urlsup-action/{urlsup-version}'` |
| `proxy`      | HTTP/HTTPS proxy URL              |                                    |
| `insecure`   | Skip SSL certificate verification | `false`                            |

### Action-Specific Options
| Input                | Description                                                         | Default    |
|----------------------|---------------------------------------------------------------------|------------|
| `urlsup-version`     | Version of urlsup to use                                            | `'latest'` |
| `create-annotations` | Create GitHub annotations for broken URLs                           | `true`     |
| `fail-on-error`      | Fail the action if broken URLs are found                            | `true`     |
| `show-performance`   | Show performance metrics in job summaries                           | `false`    |
| `telemetry`          | Enable anonymous performance telemetry and metrics in job summaries | `true`     |

## 📤 Outputs

| Output         | Description                         |
|----------------|-------------------------------------|
| `total-urls`   | Total number of URLs checked        |
| `broken-urls`  | Number of broken URLs found         |
| `success-rate` | Percentage of working URLs          |
| `report-path`  | Path to detailed JSON report        |
| `exit-code`    | Exit code from urlsup (0 = success) |

## 📖 Usage Examples

### Basic URL Checking
```yaml
- name: Check all markdown files
  id: validate-urls
  uses: simeg/urlsup-action@v2
  with:
    files: '**/*.md'
    include-extensions: 'md'
```

### Advanced Configuration
```yaml
- name: Check URLs with custom settings
  id: validate-urls
  uses: simeg/urlsup-action@v2
  with:
    files: 'docs/ README.md CHANGELOG.md'
    timeout-seconds: 15
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
  id: validate-urls
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
        id: validate-urls
        uses: simeg/urlsup-action@v2
        with:
          files: ${{ inputs.files || '**/*.md' }}
          timeout-seconds: 5
          retry: 2
          rate-limit-ms: 100
          allow-status: ${{ inputs.strict && '200' || '200,202,204' }}
          failure-threshold: ${{ inputs.strict && '' || '3' }}  # Allow 3% broken URLs in non-strict mode
          show-performance: true                                # Show detailed metrics
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

## ⚠️ Common Use Cases

### Documentation Sites
```yaml
- name: Validate documentation URLs
  id: validate-urls
  uses: simeg/urlsup-action@v2
  with:
    files: 'docs/ *.md'
    include-extensions: 'md,rst'
    allow-status: '200,202'
    exclude-pattern: 'localhost|127\.0\.0\.1'
```

### API Documentation
```yaml
- name: Validate API documentation URLs
  id: validate-urls
  uses: simeg/urlsup-action@v2
  with:
    files: 'api-docs/'
    timeout-seconds: 60
    retry: 3
    allowlist: 'api.example.com,docs.example.com'
```

### Lenient Checking with Thresholds
```yaml
# Traditional lenient approach (never fails)
- name: Non-blocking URL validation
  id: validate-urls
  uses: simeg/urlsup-action@v2
  with:
    allow-status: '200,202,204,301,302,429'
    allow-timeout: true
    fail-on-error: false

# Modern threshold approach (fails only if too many URLs are broken)
- name: URL validation with 10% tolerance
  id: validate-urls
  uses: simeg/urlsup-action@v2
  with:
    failure-threshold: "10"                 # Allow up to 10% broken URLs
    allow-status: '200,202,204,301,302,429'
    show-performance: true                  # Track performance metrics
    retry: 2
```

### Failure Threshold and Performance Monitoring
```yaml
# Allow some broken URLs with detailed performance tracking
- name: Validate URLs with tolerance and metrics
  id: validate-urls
  uses: simeg/urlsup-action@v2
  with:
    files: 'docs/ README.md'
    failure-threshold: "5"           # Allow up to 5% broken URLs
    show-performance: true           # Show detailed performance metrics
    timeout-seconds: 10
    retry: 3
    rate-limit-ms: 1500              # Be gentle with external sites
    allow-status: '200,202,204,429'  # Include rate-limited responses
```


## 📚 Documentation & Examples

- **[Examples Directory](examples/)** - Real-world workflow examples and configurations
- **[Configuration Guide](examples/configs/)** - Pre-built configuration templates
- **[Changelog](CHANGELOG.md)** - Version history and migration guides
- **[Testing Guide](TESTING.md)** - Testing infrastructure and contribution guidelines


## ❓ FAQ

### **Q: How fast is the action after the first run?**
**A:** After the first run, the action is 5-10x faster due to automatic binary caching. First run may take 1-2 minutes (compiling urlsup), subsequent runs take 10-20 seconds.

### **Q: Do I need to set up caching myself?**
**A:** No! The action automatically handles binary caching for you. No additional configuration needed.

### **Q: What file types are supported?**
**A:** By default: Markdown (`.md`), reStructuredText (`.rst`), plain text (`.txt`), and HTML (`.html`). You can customize this with the `include-extensions` input.

### **Q: How do I exclude certain URLs from validation?**
**A:** Use the `exclude-pattern` input with a regex pattern:
```yaml
exclude-pattern: 'localhost|127\.0\.0\.1|example\.com|internal\.company\.com'
```

### **Q: Can I validate private/internal URLs?**
**A:** Yes, but they need to be accessible from GitHub Actions runners. For private URLs, consider using `allowlist` or `exclude-pattern` to skip them.

### **Q: The action found broken URLs but they work in my browser. Why?**
**A:** This is common! Here's how to debug and fix:

**Common causes:**
- **Rate limiting**: Some sites block automated requests
- **User-Agent blocking**: Try setting a custom `user-agent`
- **Geoblocking**: GitHub runners are in different locations
- **Authentication required**: URLs requiring login will fail

**Debugging steps:**
1. **Check the annotations** - They now include specific suggestions for each URL
2. **Test with a custom user-agent:**
   ```yaml
   user-agent: 'Mozilla/5.0 (compatible; Documentation Bot)'
   ```
3. **Add rate limiting:**
   ```yaml
   rate-limit-ms: 2000  # 2 seconds between requests
   retry: 3
   ```
4. **Allow common "false positive" status codes:**
   ```yaml
   allow-status: '200,202,204,403,429'  # Include 403 (Forbidden) and 429 (Rate Limited)
   ```

### **Q: How do I handle rate limiting from websites?**
**A:** Use these inputs to be more respectful:
```yaml
rate-limit-ms: 1000     # 1 second between requests
retry: 3                # Retry failed requests
allow-status: '200,429' # Accept 429 (Too Many Requests)
```

### **Q: Can I run this action on a schedule?**
**A:** Yes! Perfect for monitoring link rot:
```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
```

### **Q: How do I troubleshoot specific URL failures?**
**A:** The action now provides actionable suggestions in annotations. Here are common scenarios:

**GitHub URLs failing:**
```yaml
# GitHub often rate limits, be gentle
rate-limit-ms: 1500
retry: 2
allow-status: '200,429'  # Allow rate limit responses
```

**API documentation with auth:**
```yaml
# Skip authenticated endpoints
exclude-pattern: 'api\.internal\.com|admin\.|\/auth\/'
```

**International/CDN sites:**
```yaml
# Some CDNs are geographically restricted
timeout-seconds: 10      # Increase timeout
allow-status: '200,403'  # Allow forbidden for geo-blocking
```

**Development/staging URLs:**
```yaml
# Exclude development environments
exclude-pattern: 'localhost|127\.0\.0\.1|dev\.|staging\.|\.local'
```

### **Q: How do I use failure thresholds to allow some broken URLs?**
**A:** Use the `failure-threshold` parameter to only fail the action when the percentage of broken URLs exceeds a specific threshold:

```yaml
# Allow up to 5% of URLs to be broken
- name: Validate URLs with tolerance
  id: validate-urls
  uses: simeg/urlsup-action@v2
  with:
    failure-threshold: "5"  # Fail only if >5% of URLs are broken
    files: 'docs/'
```

**Common use cases:**
- **Documentation sites**: Allow 2-5% broken links for external dependencies
- **Large repositories**: Set 1-3% threshold for legacy or external URLs
- **CI/CD pipelines**: Use higher thresholds (10-20%) for non-critical checks

**How it works:**
- If 100 URLs are found and 3 are broken (3%), action passes with `failure-threshold: "5"`
- If 100 URLs are found and 8 are broken (8%), action fails with `failure-threshold: "5"`
- Threshold information is displayed in job summaries with clear pass/fail status
- Leave empty for default behavior (any broken URL fails the action)

### **Q: How do I see performance metrics in job summaries?**
**A:** Performance metrics are automatically enabled by default and appear in GitHub job summaries when `telemetry: true` (default). The metrics include:

- **Setup Time** - How long it took to install/cache the urlsup binary
- **Validation Time** - Duration of URL checking process
- **Cache Status** - Whether the binary was cached (✅ Hit) or downloaded fresh (❌ Miss)

To explicitly enable performance metrics:
```yaml
- name: Validate URLs with telemetry
  id: validate-urls
  uses: simeg/urlsup-action@v2
  with:
    telemetry: true  # Enable performance tracking (default: true)
```

To disable performance metrics:
```yaml
- name: Validate URLs without telemetry
  id: validate-urls
  uses: simeg/urlsup-action@v2
  with:
    telemetry: false  # Disable performance tracking
```

### **Q: How do I combine failure thresholds with performance monitoring?**
**A:** You can use both features together for comprehensive URL validation:

```yaml
- name: Validate URLs with threshold and metrics
  id: validate-urls
  uses: simeg/urlsup-action@v2
  with:
    files: 'docs/ *.md'
    failure-threshold: "3"      # Allow up to 3% broken URLs
    show-performance: true      # Show detailed performance metrics
    retry: 2                    # Retry failed URLs twice
    rate-limit-ms: 1000         # Be gentle with rate limiting
```

This configuration will:
- ✅ Show detailed performance metrics in the job summary
- ✅ Display failure threshold status (3% tolerance)
- ✅ Only fail if more than 3% of URLs are broken
- ✅ Provide actionable recommendations for broken URLs

### **Q: How do I contribute or report issues?**
**A:**  Report bugs or feature requests on [GitHub Issues](https://github.com/simeg/urlsup-action/issues)


## 🔧 Migration from v1

**v1 (Docker-based):**
```yaml
- uses: simeg/urlsup-action@v1
  with:
    args: '*.md --threads 10 --allow 429'
```

**v2 (Composite with binary caching, 5-10x faster):**
```yaml
- uses: simeg/urlsup-action@v2
  with:
    files: '*.md'
    concurrency: 10
    allow-status: '200,429'
```

### Performance Improvements in v2
- **🚀 Binary Caching**: Automatic caching of urlsup binary across workflow runs
- **⚡ Faster Startup**: 5-10x faster than Docker-based v1 (seconds vs minutes)
- **🔄 Smart Cache Keys**: Version and platform-specific caching for reliability

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

## 🔧 Internal Scripts

The action uses several Python scripts located in the `scripts/` directory that handle the core functionality:

### **`scripts/validate.py`**
The main validation script that orchestrates the URL checking process.

**Key features:**
- Translates GitHub Action inputs to urlsup CLI arguments
- Executes urlsup binary with proper error handling
- Parses JSON output to extract metrics (total URLs, broken URLs, success rate)
- Sets GitHub Action outputs for use in subsequent steps
- Handles both successful and failed validation scenarios

### **`scripts/annotate.py`**
Creates GitHub annotations for broken URLs found during validation.

**Key features:**
- Parses urlsup JSON output to identify broken URLs
- Creates inline file annotations showing broken URLs with line numbers
- Supports multiple urlsup output formats for backward compatibility
- Formats error messages with HTTP status codes and detailed error information
- Gracefully handles parsing errors with fallback methods

### **`scripts/summary.py`**
Generates rich HTML job summaries for the GitHub Actions interface.

**Key features:**
- Creates formatted job summary with success metrics and visual progress bars
- Displays detailed broken URL information in organized tables
- Provides actionable recommendations for fixing different types of issues
- Includes expandable sections with technical details and metadata
- Handles both successful runs and error scenarios

### **`scripts/common.py`**
Shared utilities and helper functions used across all scripts.

**Key features:**
- Centralized logging with consistent formatting and colors
- JSON report parsing with support for multiple urlsup output formats
- File path normalization and GitHub workspace handling
- Markdown escaping for safe display in job summaries
- GitHub Actions integration utilities

The action also includes inline setup logic that:
- Installs the Rust toolchain if needed
- Downloads and installs the urlsup binary via `cargo install`
- Handles version pinning and caching through GitHub's built-in mechanisms

These components work together to provide a seamless URL validation experience with rich GitHub integration, automatic binary management, and comprehensive error reporting.

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

## 🔗 Related

- **[urlsup](https://github.com/simeg/urlsup)** - The underlying Rust CLI tool
- **[Actions Marketplace](https://github.com/marketplace/actions/url-validator)** - Find this action
- **[GitHub Actions Documentation](https://docs.github.com/en/actions)** - Learn more about workflows

## 📄 License

MIT © [Simon Egersand](https://github.com/simeg)
