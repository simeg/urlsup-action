#!/usr/bin/env python3
"""
Annotation script for urlsup - creates GitHub annotations for broken URLs.
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from common import Logger, PathUtils, ReportParser


def create_annotation(file_path: str, line: int, url: str, status: Optional[str] = None, error: Optional[str] = None) -> bool:
    """Create GitHub annotation for a broken URL."""
    # Clean up file path using shared utility
    clean_file = PathUtils.normalize_file_path(file_path)

    # Validate inputs
    if not file_path or not line or not url:
        Logger.warning(f"Invalid annotation data: file='{file_path}' line='{line}' url='{url}'", to_stderr=True)
        return False

    # Construct annotation message
    message = f"Broken URL: {url}"
    if status and status not in ("null", ""):
        message += f" (HTTP {status})"
    if error and error not in ("null", ""):
        message += f" - {error}"

    # Create GitHub annotation
    # Format: ::error file={name},line={line}::{message}
    # Explicitly write to stdout for GitHub Actions
    print(f"::error file={clean_file},line={line}::{message}", flush=True)
    return True


def process_report(report_path: str) -> int:
    """Process JSON report and create annotations."""
    if not report_path or not Path(report_path).exists():
        Logger.error(f"Report file not found: {report_path}", to_stderr=True)
        return 0

    Logger.info(f"Processing report: {report_path}", to_stderr=True)

    data = ReportParser.load_report(report_path)
    if not data:
        Logger.warning("Attempting basic parsing for annotations", to_stderr=True)
        return process_non_json_report(report_path)

    Logger.info("Using JSON parsing", to_stderr=True)

    # Detect format for better logging
    has_rich_metadata = "urls" in data and "files" in data
    format_type = "rich metadata" if has_rich_metadata else "basic"
    Logger.info(f"Detected urlsup format: {format_type}", to_stderr=True)

    # Extract failed URLs using shared parser
    issues = ReportParser.extract_issues(data)
    failed_count = 0

    for issue in issues:
        try:
            if create_annotation(
                issue.get("file", ""),
                issue.get("line", 1),
                issue.get("url", ""),
                issue.get("status_code"),
                issue.get("error"),
            ):
                failed_count += 1
        except Exception as e:
            Logger.warning(f"Failed to create annotation for issue: {e}", to_stderr=True)

    Logger.info(f"Created {failed_count} annotations for broken URLs", to_stderr=True)
    return failed_count


def process_non_json_report(report_path: str) -> int:
    """Process non-JSON output (fallback)."""
    Logger.warning("Attempting to parse non-JSON output for annotations", to_stderr=True)

    failed_count = 0

    try:
        with open(report_path) as f:
            content = f.read()

        # Look for URLs in the content that might be broken
        # This is a simplified approach and might not catch all cases

        # Look for URL patterns - this is very basic
        url_pattern = r'https?://[^\s<>"\']+[^\s<>"\'.,)]'
        urls = re.findall(url_pattern, content)

        for url in urls[:10]:  # Limit to first 10 to avoid spam
            print(f"::error::Broken URL found: {url}")
            failed_count += 1

        if failed_count == 0:
            Logger.warning("Could not parse broken URLs from report for annotations", to_stderr=True)
            Logger.info("Report content preview:", to_stderr=True)
            lines = content.split("\n")[:10]
            for line in lines:
                print(f"  {line}", file=sys.stderr)
        else:
            Logger.info(f"Created {failed_count} basic annotations for broken URLs", to_stderr=True)

    except Exception as e:
        Logger.error(f"Failed to process non-JSON report: {e}", to_stderr=True)

    return failed_count


def create_annotations() -> None:
    """Main function to create GitHub annotations."""
    Logger.info("Creating GitHub annotations for broken URLs...", to_stderr=True)

    report_path = os.environ.get("REPORT_PATH")
    if not report_path:
        Logger.error("REPORT_PATH environment variable not set", to_stderr=True)
        return

    try:
        count = process_report(report_path)
        Logger.success("Annotation processing complete", to_stderr=True)
        Logger.info(f"Total annotations created: {count}", to_stderr=True)
    except Exception as e:
        Logger.error(f"Unexpected error during annotation processing: {e}", to_stderr=True)
        Logger.warning("Continuing anyway...", to_stderr=True)


if __name__ == "__main__":
    create_annotations()
