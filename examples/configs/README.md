# Configuration Templates

This directory contains pre-configured JSON templates for common urlsup-action use cases. These configurations can be used directly with the `config` input parameter or as starting points for custom configurations.

## Available Configurations

### 📚 Documentation Sites
**File:** `documentation.json`
**Use Case:** GitBook, MkDocs, Sphinx, or similar documentation sites
**Characteristics:**
- Moderate timeouts (15s) suitable for documentation links
- Allows common redirect codes
- Includes documentation-specific allowlists
- Excludes placeholder and example URLs

```yaml
- uses: simeg/urlsup-action@v2
  with:
    config: examples/configs/documentation.json
```

### 🔌 API Documentation
**File:** `api-docs.json`
**Use Case:** REST API docs, OpenAPI specs, Postman collections
**Characteristics:**
- Long timeouts (60s) for live API endpoints
- Conservative concurrency to avoid rate limiting
- Allows authentication status codes (401, 403)
- Higher failure threshold for flaky APIs

```yaml
- uses: simeg/urlsup-action@v2
  with:
    config: examples/configs/api-docs.json
```

### 🎯 Strict Validation
**File:** `strict.json`
**Use Case:** Production environments, critical documentation
**Characteristics:**
- Only allows 200 status codes
- No retries for fast failure
- Zero failure threshold
- Excludes development and placeholder URLs

```yaml
- uses: simeg/urlsup-action@v2
  with:
    config: examples/configs/strict.json
    fail-on-error: true
```

### 🌊 Lenient Validation
**File:** `lenient.json`
**Use Case:** Development environments, CI with external dependencies
**Characteristics:**
- Allows many status codes including rate limiting
- High timeout and retry tolerance
- 15% failure threshold
- Comprehensive allowlists for common sites

```yaml
- uses: simeg/urlsup-action@v2
  with:
    config: examples/configs/lenient.json
    fail-on-error: false
```

### ⚡ High Performance
**File:** `performance.json`
**Use Case:** Large repositories, time-sensitive CI pipelines
**Characteristics:**
- Short timeouts (5s) and minimal retries
- High concurrency (50 concurrent requests)
- Focused allowlist for reliability
- Optimized for speed over thoroughness

```yaml
- uses: simeg/urlsup-action@v2
  with:
    config: examples/configs/performance.json
```

## Using Configuration Files

### Method 1: Direct Reference
Reference a configuration file directly in your workflow:

```yaml
- uses: simeg/urlsup-action@v2
  with:
    config: examples/configs/documentation.json
    files: 'docs/ README.md'
```

### Method 2: Copy and Customize
1. Copy a template to your repository:
   ```bash
   cp examples/configs/documentation.json .urlsup.json
   ```

2. Customize for your needs:
   ```json
   {
     "timeout": 20,
     "allowlist": ["yourdomain.com", "github.com"],
     "exclude_patterns": ["localhost", "staging\\."]
   }
   ```

3. Reference in workflow:
   ```yaml
   - uses: simeg/urlsup-action@v2
     with:
       config: .urlsup.json
   ```

### Method 3: Override Specific Settings
Use a config file as base and override specific settings:

```yaml
- uses: simeg/urlsup-action@v2
  with:
    config: examples/configs/documentation.json
    timeout: 30                           # Override timeout from config
    allowlist: 'mydomain.com,github.com'  # Override allowlist
```

## Configuration Parameters

### Network Settings
| Parameter     | Description                 | Example |
|---------------|-----------------------------|---------|
| `timeout`     | Request timeout in seconds  | `15`    |
| `retry`       | Number of retry attempts    | `3`     |
| `retry_delay` | Delay between retries (ms)  | `2000`  |
| `concurrency` | Concurrent requests         | `20`    |
| `rate_limit`  | Delay between requests (ms) | `200`   |

### URL Filtering
| Parameter           | Description                  | Example                           |
|---------------------|------------------------------|-----------------------------------|
| `allow_status`      | Allowed HTTP status codes    | `[200, 301, 302]`                 |
| `allowlist`         | Domains to always allow      | `["github.com", "*.example.com"]` |
| `exclude_patterns`  | URL patterns to skip         | `["localhost", "staging\\."]`     |
| `allow_timeout`     | Allow URLs that timeout      | `true`                            |
| `failure_threshold` | Max % of broken URLs allowed | `10`                              |

### File Processing
| Parameter | Description              | Example                      |
|-----------|--------------------------|------------------------------|
| `include` | File extensions to check | `["md", "rst", "html"]`      |
| `exclude` | Directories to skip      | `["node_modules/", ".git/"]` |

### Advanced Options
| Parameter    | Description              | Example               |
|--------------|--------------------------|-----------------------|
| `user_agent` | Custom User-Agent header | `"my-checker/1.0"`    |
| `proxy`      | HTTP/HTTPS proxy URL     | `"http://proxy:8080"` |
| `insecure`   | Skip SSL verification    | `false`               |

## Best Practices

### 1. Start Simple
Begin with a basic configuration and add complexity as needed:
```json
{
  "timeout": 10,
  "retry": 2,
  "allow_status": [200, 301, 302]
}
```

### 2. Environment-Specific Configs
Use different configurations for different environments:
- `config-dev.json` - Lenient for development
- `config-staging.json` - Moderate for staging
- `config-prod.json` - Strict for production

### 3. Domain-Specific Allowlists
Create focused allowlists for your ecosystem:
```json
{
  "allowlist": [
    "docs.mycompany.com",
    "api.mycompany.com",
    "github.com/myorg",
    "mycompany.atlassian.net"
  ]
}
```

### 4. Gradual Strictness
Implement progressively stricter validation:
1. Start with `lenient.json` to identify issues
2. Move to `documentation.json` for regular checks
3. Use `strict.json` for production releases

### 5. Performance Tuning
Adjust concurrency and timeouts based on your infrastructure:
- **Fast network:** High concurrency, low timeout
- **Slow network:** Low concurrency, high timeout
- **Rate-limited APIs:** Low concurrency, high rate_limit

## Troubleshooting Configurations

### Common Issues

**Too many timeouts?**
```json
{
  "timeout": 30,
  "retry": 3,
  "allow_timeout": true
}
```

**Rate limiting errors?**
```json
{
  "rate_limit": 1000,
  "concurrency": 5,
  "allow_status": [200, 429]
}
```

**False positives?**
```json
{
  "exclude_patterns": [
    "localhost",
    "staging\\.",
    "placeholder\\."
  ]
}
```

**Performance too slow?**
```json
{
  "timeout": 5,
  "retry": 1,
  "concurrency": 30,
  "rate_limit": 100
}
```

## Custom Configuration Schema

For advanced users, create configurations following the urlsup schema:

```json
{
  "$schema": "https://raw.githubusercontent.com/simeg/urlsup/main/schema.json",
  "description": "Custom configuration for my project",
  "timeout": 15,
  "// ... other settings": "..."
}
```

This enables IDE validation and autocompletion for configuration files.