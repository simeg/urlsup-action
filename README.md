# urlsup-action
GitHub Action to check if URLs in your repo are up and available

## Usage

This is a GitHub Action to check if URLs in your repo are up and available
(HTTP status code == 200). It uses [`urlsup`](https://github.com/simeg/urlsup)
which is built in Rust and is very fast.

## Inputs

### `args`

**Required**. The args to be passed to
[`urlsup`](https://github.com/simeg/urlsup).

## Example action workflow

```yaml
name: Validate that links are up
on: push

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2  # Required for urlsup

      # This step writes the files with URLs to the env variable $FILES_TO_CHECK to be used for the later step
      - name: Find files with links
        shell: bash
        run: |
          echo 'FILES_TO_CHECK<<EOF' >> $GITHUB_ENV
          
          # --- This is where we define what files to check ---

          # $GITHUB_WORKSPACE is where our files live
          # Ignore dirs and only include markdown files
          
          files_to_check=$(find $GITHUB_WORKSPACE -type f \
          -not -path '*/\.git/*' -not -path '*/\.github/*' \
          -name "*.md")
          
          echo $files_to_check >> $GITHUB_ENV
          echo 'EOF' >> $GITHUB_ENV

      - name: Validate that links are up
        uses: simeg/urlsup-action@v1.0.0
        with:
          # Pass the files and any additional arguments to urlsup
          args: ${{ env.FILES_TO_CHECK }} --threads 10 --allow 429 --white-list http://localhost
```
