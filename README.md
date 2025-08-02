# urlsup-action
GitHub Action to check if URLs in your repo are up and available. Supports scheduled runs and manual execution with custom file patterns.

## Usage

This is a GitHub Action to check if URLs in your repo are up and available
(HTTP status code == 200). It uses [`urlsup`](https://github.com/simeg/urlsup)
which is built in Rust and is very fast.

The action can be configured to run:
- **On a schedule** (e.g., weekly) to catch broken links over time
- **Manually** via the GitHub Actions UI with customizable file patterns and options
- **On pushes or pull requests** for immediate validation

## Inputs

### Action Inputs

#### `args`
**Required**. The arguments to be passed to [`urlsup`](https://github.com/simeg/urlsup).

### Manual Trigger Inputs

When using `workflow_dispatch`, you can customize the action through the GitHub UI:

#### `file_pattern`
**Optional**. File pattern to check (default: `*.md`).
- Examples: `*.md`, `README.md`, `docs/*.rst`, `*.md *.txt`

#### `extra_args`
**Optional**. Extra arguments for urlsup (default: `--threads 10 --allow 429`).
- Examples: `--timeout 30`, `--allow 404 --threads 5`

See the [urlsup documentation](https://github.com/simeg/urlsup?tab=readme-ov-file#usage) for more details on available options.

## Example action workflow

```yaml
name: Validate that links are up

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  pull_request:          # Run on pull requests
  workflow_dispatch:     # Allow manual trigger
    inputs:
      file_pattern:      # Allow specifying a file pattern to check in Github Actions UI
        description: 'File pattern to check (default: *.md)'
        required: false
        default: '*.md'
      extra_args:
        description: 'Extra arguments for urlsup'
        required: false
        default: '--threads 10 --allow 429'

permissions:
  contents: read  # Only need read access to repository files

concurrency:
  group: link-check           # Prevent multiple link-check workflows from running simultaneously
  cancel-in-progress: true    # Cancel older runs when new ones start

jobs:
  check-links:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Find files to check
        id: find-files
        run: |
          # Use specified pattern (from manual trigger) or default to *.md for markdown files
          pattern="${{ inputs.file_pattern || '*.md' }}"
          # Find files matching pattern, exclude hidden directories, convert to space-separated list
          echo "files=$(find . -name "$pattern" -not -path './.*' -type f | tr '\n' ' ')" >> $GITHUB_OUTPUT

      - name: Validate that links are up
        uses: simeg/urlsup-action@v1.0.0
        with:
          args: ${{ steps.find-files.outputs.files }} ${{ inputs.extra_args || '--threads 10 --allow 429' }} --white-list http://localhost
```

## Manual Execution

To run the workflow manually:

1. Go to your repository's **Actions** tab
2. Click on your workflow name in the left sidebar
3. Click the **"Run workflow"** button
4. Customize the inputs if needed:
   - **File pattern**: Specify which files to check (e.g., `docs/*.md`, `README.md`)
   - **Extra arguments**: Add custom urlsup options (e.g., `--timeout 30 --allow 404`)
5. Click **"Run workflow"**

## Common Use Cases

- **Weekly link maintenance**: Schedule runs to catch broken links over time
- **Documentation-specific checks**: Use `docs/*.md` pattern for documentation files
- **Custom tolerance**: Use `--allow 404 --allow 429` for sites with temporary issues
- **Faster execution**: Use `--threads 20` for larger repositories
