#!/usr/bin/env python3
"""
Annotation script for urlsup - creates GitHub annotations for broken URLs.
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
    """Log info message to stderr."""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}", file=sys.stderr)


def log_success(message):
    """Log success message to stderr."""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}", file=sys.stderr)


def log_warning(message):
    """Log warning message to stderr."""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}", file=sys.stderr)


def log_error(message):
    """Log error message to stderr."""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}", file=sys.stderr)


def create_annotation(file_path, line, url, status=None, error=None):
    """Create GitHub annotation for a broken URL."""
    # Clean up file path (remove leading ./)
    clean_file = str(Path(file_path).as_posix()).lstrip('./')
    
    # Validate inputs
    if not file_path or not line or not url:
        log_warning(f"Invalid annotation data: file='{file_path}' line='{line}' url='{url}'")
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


def process_report(report_path):
    """Process JSON report and create annotations."""
    if not report_path or not Path(report_path).exists():
        log_error(f"Report file not found: {report_path}")
        return 0
    
    log_info(f"Processing report: {report_path}")
    
    try:
        with open(report_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse JSON report: {e}")
        log_warning("Attempting basic parsing for annotations")
        return process_non_json_report(report_path)
    except Exception as e:
        log_error(f"Failed to read report file: {e}")
        return 0
    
    log_info("Using JSON parsing")
    
    # Extract failed URLs using different possible JSON structures
    failed_count = 0
    
    # Try urlsup v2.2.0 format (.issues[])
    issues = data.get('issues', [])
    if issues:
        for issue in issues:
            try:
                if create_annotation(
                    issue.get('file', ''),
                    issue.get('line', 1),
                    issue.get('url', ''),
                    issue.get('status_code'),
                    issue.get('description') or issue.get('error')
                ):
                    failed_count += 1
            except Exception as e:
                log_warning(f"Failed to create annotation for issue: {e}")
    
    # Try older format (.failed_urls[])
    if failed_count == 0:
        failed_urls = data.get('failed_urls', [])
        for item in failed_urls:
            try:
                if create_annotation(
                    item.get('file', ''),
                    item.get('line', 1),
                    item.get('url', ''),
                    item.get('status_code'),
                    item.get('error')
                ):
                    failed_count += 1
            except Exception as e:
                log_warning(f"Failed to create annotation for failed URL: {e}")
    
    # Try alternative older JSON structure (.results[])
    if failed_count == 0:
        results = data.get('results', [])
        for result in results:
            # Check if this result represents a failure
            success = result.get('success')
            if success is False or (result.get('result', {}).get('success') is False):
                try:
                    location = result.get('location', {})
                    result_data = result.get('result', {})
                    
                    if create_annotation(
                        location.get('file') or result.get('file', ''),
                        location.get('line') or result.get('line', 1),
                        result.get('url', ''),
                        result_data.get('status_code') or result.get('status_code'),
                        result_data.get('error') or result.get('error')
                    ):
                        failed_count += 1
                except Exception as e:
                    log_warning(f"Failed to create annotation for result: {e}")
    
    log_info(f"Created {failed_count} annotations for broken URLs")
    return failed_count


def process_non_json_report(report_path):
    """Process non-JSON output (fallback)."""
    log_warning("Attempting to parse non-JSON output for annotations")
    
    failed_count = 0
    
    try:
        with open(report_path) as f:
            content = f.read()
        
        # Look for URLs in the content that might be broken
        # This is a simplified approach and might not catch all cases
        import re
        
        # Look for URL patterns - this is very basic
        url_pattern = r'https?://[^\s<>"\']+[^\s<>"\'.,)]'
        urls = re.findall(url_pattern, content)
        
        for url in urls[:10]:  # Limit to first 10 to avoid spam
            print(f"::error::Broken URL found: {url}")
            failed_count += 1
        
        if failed_count == 0:
            log_warning("Could not parse broken URLs from report for annotations")
            log_info("Report content preview:")
            lines = content.split('\n')[:10]
            for line in lines:
                print(f"  {line}", file=sys.stderr)
        else:
            log_info(f"Created {failed_count} basic annotations for broken URLs")
    
    except Exception as e:
        log_error(f"Failed to process non-JSON report: {e}")
    
    return failed_count


def create_annotations():
    """Main function to create GitHub annotations."""
    log_info("Creating GitHub annotations for broken URLs...")
    
    report_path = os.environ.get('REPORT_PATH')
    if not report_path:
        log_error("REPORT_PATH environment variable not set")
        return
    
    try:
        count = process_report(report_path)
        log_success("Annotation processing complete")
        log_info(f"Total annotations created: {count}")
    except Exception as e:
        log_error(f"Unexpected error during annotation processing: {e}")
        log_warning("Continuing anyway...")


if __name__ == "__main__":
    create_annotations()