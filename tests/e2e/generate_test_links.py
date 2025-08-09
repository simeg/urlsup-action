#!/usr/bin/env python3
"""
Generate test links for end-to-end testing of urlsup-action.
Based on: https://github.com/simeg/urlsup/blob/master/scripts/generate_test_links.py
"""

from pathlib import Path


def generate_test_repository(base_dir: Path):
    """Generate a test repository with mixed URL scenarios."""
    test_dir = base_dir / "test-links-dir"

    # Create directory structure
    dir_one = test_dir / "dir-one"
    dir_two = dir_one / "dir-two"
    dir_two.mkdir(parents=True, exist_ok=True)

    # File 1: Working URLs
    working_urls_content = """# Working URLs Test

These URLs should all work:

- [GitHub](https://github.com)
- [Example Domain](https://example.com)
- [Google](https://www.google.com)
- [Stack Overflow](https://stackoverflow.com)
- [Python.org](https://python.org)
- [Mozilla](https://www.mozilla.org)
- [W3C](https://www.w3.org)

## Documentation Links

- [GitHub Actions](https://docs.github.com/en/actions)
- [Python Docs](https://docs.python.org/3/)

## API Endpoints

- [GitHub API](https://api.github.com)
- [HTTPBin](https://httpbin.org/get)
"""

    # File 2: Broken URLs
    broken_urls_content = """# Broken URLs Test

These URLs should fail:

- [Non-existent Domain](https://this-domain-does-not-exist-12345.com)
- [Bad Subdomain](https://nonexistent.github.com)
- [Invalid TLD](https://example.invalidtld)
- [Unreachable Port](https://httpbin.org:99999)
- [404 Page](https://httpstat.us/404)
- [500 Error](https://httpstat.us/500)
- [Timeout URL](https://httpstat.us/408)

## Local URLs (should fail in CI)

- [Localhost](http://localhost:3000)
- [127.0.0.1](http://127.0.0.1:8080)

## Malformed URLs

- [Missing Protocol](www.example.com)
- [Invalid Characters](https://example.com/path with spaces)
"""

    # File 3: Mixed URLs
    mixed_urls_content = """# Mixed URLs Test

This file contains a mix of working and broken URLs.

## Working Section

- [GitHub](https://github.com)
- [Example](https://example.com)

## Broken Section

- [Non-existent](https://this-does-not-exist-12345.com)
- [404 Error](https://httpstat.us/404)

## Edge Cases

- [Redirect](https://httpstat.us/301)
- [Slow Response](https://httpstat.us/200?sleep=2000)

## Different File Types

Check these documentation files:
- [README](https://raw.githubusercontent.com/simeg/urlsup/main/README.md)
- [License](https://raw.githubusercontent.com/simeg/urlsup/main/LICENSE)
"""

    # File 4: Configuration test
    config_test_content = """# Configuration Test

This file tests various URL patterns for filtering.

## Should be excluded by pattern
- [Local Development](http://localhost:3000/api)
- [Another Local](http://127.0.0.1:8080)

## Should be allowed by allowlist
- [GitHub API](https://api.github.com/users/simeg)
- [GitHub Main](https://github.com/simeg/urlsup)

## Various status codes
- [200 OK](https://httpstat.us/200)
- [201 Created](https://httpstat.us/201)
- [202 Accepted](https://httpstat.us/202)
- [204 No Content](https://httpstat.us/204)
- [301 Redirect](https://httpstat.us/301)
- [404 Not Found](https://httpstat.us/404)
- [500 Server Error](https://httpstat.us/500)
- [503 Unavailable](https://httpstat.us/503)
"""

    # Write files
    (dir_one / "working-urls.md").write_text(working_urls_content)
    (dir_one / "broken-urls.md").write_text(broken_urls_content)
    (dir_two / "mixed-urls.md").write_text(mixed_urls_content)
    (test_dir / "config-test.md").write_text(config_test_content)

    # Create additional file types for extension testing
    (test_dir / "urls.txt").write_text("https://example.com\nhttps://broken-link.invalid")
    (test_dir / "documentation.rst").write_text(
        """
Test RST File
=============

Links in reStructuredText:

- `GitHub <https://github.com>`_
- `Broken Link <https://broken.invalid>`_
"""
    )

    # Create HTML file
    (test_dir / "page.html").write_text(
        """
<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body>
    <a href="https://example.com">Working Link</a>
    <a href="https://broken.invalid">Broken Link</a>
</body>
</html>
"""
    )

    print(f"✅ Generated test repository structure in: {test_dir}")
    print("\nTest files created:")
    print(f"  📄 {dir_one}/working-urls.md (working URLs)")
    print(f"  📄 {dir_one}/broken-urls.md (broken URLs)")
    print(f"  📄 {dir_two}/mixed-urls.md (mixed URLs)")
    print(f"  📄 {test_dir}/config-test.md (configuration tests)")
    print(f"  📄 {test_dir}/urls.txt (plain text)")
    print(f"  📄 {test_dir}/documentation.rst (reStructuredText)")
    print(f"  📄 {test_dir}/page.html (HTML)")

    return test_dir


if __name__ == "__main__":
    generate_test_repository(Path.cwd())
