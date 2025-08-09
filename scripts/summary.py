#!/usr/bin/env python3
"""Summary script for urlsup - generates rich HTML job summaries for GitHub Actions."""

import os
from pathlib import Path
from typing import Any, Dict, List

from common import GitHubActions, Logger, ReportParser, ValidationUtils


def parse_broken_urls_from_report(report_path: str) -> List[Dict[str, Any]]:
    """Parse broken URLs from the JSON report for detailed breakdown."""
    if not report_path or not Path(report_path).exists():
        return []

    data = ReportParser.load_report(report_path)
    if not data:
        return []

    # Extract issues using shared parser
    issues = ReportParser.extract_issues(data)

    # Format for summary display
    broken_urls = []
    for issue in issues:
        broken_urls.append(
            {
                "file": issue.get("file", "unknown"),
                "line": issue.get("line", 1),
                "url": issue.get("url", ""),
                "status_code": issue.get("status_code", "N/A"),
                "error": issue.get("error", "N/A"),
            }
        )

    return broken_urls[:20]  # Limit to first 20 to avoid huge summaries


def escape_markdown(text: Any) -> str:
    """Escape text for safe inclusion in markdown."""
    return ValidationUtils.escape_markdown(text)


def generate_summary() -> None:
    """Generate job summary."""
    total_urls = int(os.environ.get("TOTAL_URLS", "0"))
    broken_urls = int(os.environ.get("BROKEN_URLS", "0"))
    success_rate = os.environ.get("SUCCESS_RATE", "0%")
    exit_code = int(os.environ.get("EXIT_CODE", "0"))
    report_path = os.environ.get("REPORT_PATH", "")

    # Rich metadata (will be 0 if not available)
    total_files = int(os.environ.get("TOTAL_FILES", "0"))
    processed_files = int(os.environ.get("PROCESSED_FILES", "0"))
    total_found_urls = int(os.environ.get("TOTAL_FOUND_URLS", "0"))
    unique_urls = int(os.environ.get("UNIQUE_URLS", "0"))
    status = os.environ.get("STATUS", "unknown")

    # Calculate working URLs
    working_urls = total_urls - broken_urls

    # Determine status and emoji
    if exit_code != 0:
        status_emoji = "❌"
        status_text = "Some URLs are broken"
        status_color = "red"
    elif total_urls == 0:
        status_emoji = "⚠️"
        status_text = "No URLs found"
        status_color = "yellow"
    else:
        status_emoji = "✅"
        status_text = "All URLs are working"
        status_color = "green"

    github_step_summary = GitHubActions.get_step_summary_file()
    if not github_step_summary:
        Logger.warning("GITHUB_STEP_SUMMARY not set, cannot generate summary")
        return

    # Start building the summary with enhanced metadata
    summary_content = f"""# {status_emoji} URL Validation Report

## Summary

| Metric | Value |
|--------|-------|
| **Status** | <span style="color: {status_color};">{status_text}</span> |
| **Total URLs Validated** | {total_urls} |
| **Working URLs** | {working_urls} |
| **Broken URLs** | {broken_urls} |
| **Success Rate** | {success_rate} |"""

    # Add rich metadata if available
    if total_files > 0 or total_found_urls > 0:
        summary_content += f"""
| **Files Processed** | {processed_files}/{total_files} |
| **Total URLs Found** | {total_found_urls} |
| **Unique URLs** | {unique_urls} |"""

        if unique_urls > 0 and total_found_urls > 0:
            duplicate_urls = total_found_urls - unique_urls
            summary_content += f"""
| **Duplicate URLs** | {duplicate_urls} |"""

    summary_content += "\n\n"
    """

"""

    # Add detailed breakdown if there are broken URLs
    if broken_urls > 0 and report_path:
        summary_content += "## Broken URLs Details\n\n"

        broken_url_details = parse_broken_urls_from_report(report_path)
        if broken_url_details:
            summary_content += "| File | Line | URL | Status | Error |\n"
            summary_content += "|------|------|-----|--------|-------|\n"

            for item in broken_url_details:
                file_path = escape_markdown(item["file"]).lstrip("./")
                line = item["line"]
                url = escape_markdown(item["url"])
                status = escape_markdown(item["status_code"])
                error = escape_markdown(item["error"])

                summary_content += f"| `{file_path}` | {line} | {url} | {status} | {error} |\n"

            summary_content += "\n"
        else:
            summary_content += (
                "**Note:** Could not parse detailed breakdown from report. "
                "See the uploaded report artifact for full details.\n\n"
            )

    # Add recommendations
    summary_content += "## Recommendations\n\n"

    if broken_urls > 0:
        summary_content += """- 🔍 **Review broken URLs** above and fix or remove them
- 🔄 **Check if URLs are temporarily down** - consider retrying
- ⚙️ **Consider allowlisting** URLs that are expected to be unavailable
- 📋 **Use exclude patterns** for URLs that should not be checked

"""
    else:
        summary_content += """- ✨ **Great job!** All URLs in your repository are working
- 🔄 **Consider scheduling** regular URL checks to catch broken links early
- 📊 **Monitor trends** by comparing reports over time

"""

    # Add action information
    github_run_id = GitHubActions.get_run_id()
    summary_content += f"""
---

<details>
<summary>📋 Action Details</summary>

- **Action:** [urlsup-action](https://github.com/simeg/urlsup-action)
- **Tool:** [urlsup](https://github.com/simeg/urlsup)
- **Report:** Available as workflow artifact
- **Run ID:** {github_run_id}

</details>"""

    # Write the summary
    try:
        with open(github_step_summary, "a") as f:
            f.write(summary_content)
        Logger.success("Job summary generated")
    except Exception as e:
        Logger.error(f"Failed to write job summary: {e}")


def main() -> None:
    """Execute job summary generation."""
    Logger.info("Generating job summary...")

    try:
        generate_summary()
        Logger.success("Job summary complete")
    except Exception as e:
        Logger.error(f"Failed to generate job summary: {e}")


if __name__ == "__main__":
    main()
