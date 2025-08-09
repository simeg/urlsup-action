# Example Workflows

This directory contains real-world examples of how to use the urlsup-action in different scenarios. Each workflow demonstrates specific use cases and configurations.

## Available Examples

### Basic Examples
- **[basic-validation.yml](workflows/basic-validation.yml)** - Simple URL validation for documentation
- **[scheduled-checks.yml](workflows/scheduled-checks.yml)** - Weekly scheduled URL validation
- **[pull-request-checks.yml](workflows/pull-request-checks.yml)** - Validate URLs in pull requests

### Advanced Examples
- **[multi-environment.yml](workflows/multi-environment.yml)** - Different configs for staging/production
- **[custom-filtering.yml](workflows/custom-filtering.yml)** - Advanced allowlist and exclude patterns
- **[performance-optimized.yml](workflows/performance-optimized.yml)** - High-performance configuration
- **[failure-threshold.yml](workflows/failure-threshold.yml)** - Allow some broken URLs with thresholds

### Specialized Use Cases
- **[documentation-site.yml](workflows/documentation-site.yml)** - For documentation websites (GitBook, MkDocs, etc.)
- **[api-documentation.yml](workflows/api-documentation.yml)** - API documentation with longer timeouts
- **[monorepo.yml](workflows/monorepo.yml)** - Multiple projects in one repository
- **[external-links-only.yml](workflows/external-links-only.yml)** - Check only external links
- **[notification-integration.yml](workflows/notification-integration.yml)** - Integrate with Slack/Teams/Discord

### Configuration Examples
- **[configs/](configs/)** - Reusable configuration files for different scenarios
- **[templates/](templates/)** - Workflow templates for quick setup

## Quick Start

1. **Copy a workflow** that matches your use case to `.github/workflows/`
2. **Customize the inputs** according to your needs
3. **Test the workflow** by creating a pull request or manual trigger
4. **Adjust configuration** based on your results

## Configuration Guide

### Common Input Patterns

```yaml
# Basic setup
- uses: simeg/urlsup-action@v2
  with:
    files: '**/*.md'
    timeout: 5
    retry: 2

# Performance optimized
- uses: simeg/urlsup-action@v2
  with:
    files: 'docs/ README.md'
    concurrency: 20
    timeout: 15
    retry: 3
    rate-limit: 50

# Lenient checking
- uses: simeg/urlsup-action@v2
  with:
    allow-status: '200,202,204,301,302,429'
    allow-timeout: true
    fail-on-error: false
    failure-threshold: 10

# Strict validation
- uses: simeg/urlsup-action@v2
  with:
    allow-status: '200'
    timeout: 10
    retry: 0
    fail-on-error: true
```

### File Selection Patterns

```yaml
# Documentation files only
files: '**/*.md *.rst docs/'

# Multiple specific files
files: 'README.md CHANGELOG.md docs/api.md'

# Exclude certain directories
files: '.'
exclude-pattern: 'node_modules|\.git|build|dist'

# Include specific extensions
include-extensions: 'md,rst,txt,html'
```

### Filtering Patterns

```yaml
# Allow specific domains
allowlist: 'github.com,docs.github.com,stackoverflow.com'

# Exclude local and example URLs
exclude-pattern: 'localhost|127\.0\.0\.1|example\.com|todo\.example'

# Allow redirects and rate limiting
allow-status: '200,201,202,204,301,302,429'
```

## Integration Patterns

### With Other Actions

```yaml
# Run after deployment
needs: deploy
if: success()

# Matrix testing across environments
strategy:
  matrix:
    environment: [staging, production]

# Conditional on file changes
if: contains(github.event.head_commit.modified, '.md')
```

### Error Handling

```yaml
# Continue on error but report
continue-on-error: true

# Use different thresholds per environment
failure-threshold: ${{ github.ref == 'refs/heads/main' && '0' || '5' }}

# Custom failure messages
- name: Report broken links
  if: failure()
  run: echo "Found broken links - check annotations for details"
```

## Best Practices

1. **Start with basic validation** and gradually add complexity
2. **Use appropriate timeouts** for your content (5s for fast sites, 30s+ for APIs)
3. **Set reasonable retry counts** (2-3 retries for flaky links)
4. **Use allowlists** for domains you trust
5. **Exclude development URLs** (localhost, staging environments)
6. **Schedule regular checks** to catch broken links early
7. **Use failure thresholds** in non-critical environments
8. **Monitor trends** by comparing reports over time

## Troubleshooting

### Common Issues

**Too many timeouts?**
- Increase `timeout` and `retry-delay`
- Reduce `concurrency`
- Use `allow-timeout: true` for flaky endpoints

**Rate limiting errors?**
- Increase `rate-limit` delay
- Add domains to `allowlist`
- Use `allow-status: '429'`

**False positives?**
- Use `exclude-pattern` for problematic URLs
- Add specific domains to `allowlist`
- Adjust `allow-status` codes

**Performance issues?**
- Increase `concurrency` (but watch rate limits)
- Use `include-extensions` to limit file types
- Be more specific with `files` input

## Contributing Examples

Have a useful configuration or workflow? Please contribute!

1. Create a new file in the appropriate directory
2. Include clear comments explaining the use case
3. Add documentation to this README
4. Submit a pull request

## Support

- 📖 [Main README](../README.md) - Full action documentation
- 🐛 [Issues](https://github.com/simeg/urlsup-action/issues) - Report problems
- 💬 [Discussions](https://github.com/simeg/urlsup-action/discussions) - Ask questions