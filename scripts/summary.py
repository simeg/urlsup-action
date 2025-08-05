#!/usr/bin/env python3
"""
Summary script for urlsup - generates rich HTML job summaries for GitHub Actions.
"""

import os
import sys
import json
from pathlib import Path


class Colors:
    """ANSI color codes for console output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def log_info(message):
    """Log info message to stdout."""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")


def log_success(message):
    """Log success message to stdout."""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


def log_warning(message):
    """Log warning message to stdout."""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


def log_error(message):
    """Log error message to stdout."""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def parse_broken_urls_from_report(report_path):
    """Parse broken URLs from the JSON report for detailed breakdown."""
    if not report_path or not Path(report_path).exists():
        return []
    
    try:
        with open(report_path) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return []
    
    broken_urls = []
    
    # Try urlsup v2.2.0 format (.issues[])
    issues = data.get('issues', [])
    for issue in issues:
        broken_urls.append({
            'file': issue.get('file', 'unknown'),
            'line': issue.get('line', 1),
            'url': issue.get('url', ''),
            'status_code': issue.get('status_code', 'N/A'),
            'error': issue.get('description') or issue.get('error', 'N/A')
        })
    
    # Try older format (.failed_urls[])
    if not broken_urls:
        failed_urls = data.get('failed_urls', [])
        for item in failed_urls:
            broken_urls.append({
                'file': item.get('file', 'unknown'),
                'line': item.get('line', 1),
                'url': item.get('url', ''),
                'status_code': item.get('status_code', 'N/A'),
                'error': item.get('error', 'N/A')
            })
    
    # Try alternative older JSON structure (.results[])
    if not broken_urls:
        results = data.get('results', [])
        for result in results:
            success = result.get('success')
            if success is False or (result.get('result', {}).get('success') is False):
                location = result.get('location', {})
                result_data = result.get('result', {})
                
                broken_urls.append({
                    'file': location.get('file') or result.get('file', 'unknown'),
                    'line': location.get('line') or result.get('line', 1),
                    'url': result.get('url', ''),
                    'status_code': result_data.get('status_code') or result.get('status_code', 'N/A'),
                    'error': result_data.get('error') or result.get('error', 'N/A')
                })
    
    return broken_urls[:20]  # Limit to first 20 to avoid huge summaries


def escape_markdown(text):
    """Escape text for safe inclusion in markdown."""
    # Replace pipe characters to avoid breaking tables
    return str(text).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def generate_progress_bar(success_percentage):
    """Generate a progress bar visualization."""
    bar_length = 20
    filled_length = int(success_percentage * bar_length / 100)
    
    progress_bar = '█' * filled_length + '░' * (bar_length - filled_length)
    return progress_bar


def generate_summary():
    """Generate job summary."""
    total_urls = int(os.environ.get('TOTAL_URLS', '0'))
    broken_urls = int(os.environ.get('BROKEN_URLS', '0'))
    success_rate = os.environ.get('SUCCESS_RATE', '0%')
    exit_code = int(os.environ.get('EXIT_CODE', '0'))
    report_path = os.environ.get('REPORT_PATH', '')
    
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
    
    github_step_summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if not github_step_summary:
        log_warning("GITHUB_STEP_SUMMARY not set, cannot generate summary")
        return
    
    # Start building the summary
    summary_content = f"""# {status_emoji} URL Validation Report

## Summary

| Metric | Value |
|--------|-------|
| **Status** | <span style="color: {status_color};">{status_text}</span> |
| **Total URLs** | {total_urls} |
| **Working URLs** | {working_urls} |
| **Broken URLs** | {broken_urls} |
| **Success Rate** | {success_rate} |

"""
    
    # Add progress bar visualization
    if total_urls > 0:
        success_percentage = int(success_rate.rstrip('%'))
        progress_bar = generate_progress_bar(success_percentage)
        
        summary_content += f"""## Progress

```
{progress_bar} {success_rate}
```

"""
    
    # Add detailed breakdown if there are broken URLs
    if broken_urls > 0 and report_path:
        summary_content += "## Broken URLs Details\n\n"
        
        broken_url_details = parse_broken_urls_from_report(report_path)
        if broken_url_details:
            summary_content += "| File | Line | URL | Status | Error |\n"
            summary_content += "|------|------|-----|--------|-------|\n"
            
            for item in broken_url_details:
                file_path = escape_markdown(item['file']).lstrip('./')
                line = item['line']
                url = escape_markdown(item['url'])
                status = escape_markdown(item['status_code'])
                error = escape_markdown(item['error'])
                
                summary_content += f"| `{file_path}` | {line} | {url} | {status} | {error} |\n"
            
            summary_content += "\n"
        else:
            summary_content += "**Note:** Could not parse detailed breakdown from report. See the uploaded report artifact for full details.\n\n"
    
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
    github_run_id = os.environ.get('GITHUB_RUN_ID', 'N/A')
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
        with open(github_step_summary, 'a') as f:
            f.write(summary_content)
        log_success("Job summary generated")
    except Exception as e:
        log_error(f"Failed to write job summary: {e}")


def main():
    """Main execution function."""
    log_info("Generating job summary...")
    
    try:
        generate_summary()
        log_success("Job summary complete")
    except Exception as e:
        log_error(f"Failed to generate job summary: {e}")


if __name__ == "__main__":
    main()