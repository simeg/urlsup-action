#!/usr/bin/env python3
"""
Common utilities and shared functionality for urlsup-action scripts.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class Colors:
    """ANSI color codes for console output."""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


class Logger:
    """Centralized logging functionality."""

    @staticmethod
    def info(message: str, to_stderr: bool = False) -> None:
        """Log info message."""
        output = sys.stderr if to_stderr else sys.stdout
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}", file=output)

    @staticmethod
    def success(message: str, to_stderr: bool = False) -> None:
        """Log success message."""
        output = sys.stderr if to_stderr else sys.stdout
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}", file=output)

    @staticmethod
    def warning(message: str, to_stderr: bool = False) -> None:
        """Log warning message."""
        output = sys.stderr if to_stderr else sys.stdout
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}", file=output)

    @staticmethod
    def error(message: str, to_stderr: bool = False) -> None:
        """Log error message."""
        output = sys.stderr if to_stderr else sys.stdout
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}", file=output)


class GitHubActions:
    """GitHub Actions environment and output utilities."""

    @staticmethod
    def get_workspace() -> str:
        """Get GitHub workspace directory."""
        return os.environ.get("GITHUB_WORKSPACE", ".")

    @staticmethod
    def get_output_file() -> Optional[str]:
        """Get GitHub output file path."""
        return os.environ.get("GITHUB_OUTPUT")

    @staticmethod
    def get_step_summary_file() -> Optional[str]:
        """Get GitHub step summary file path."""
        return os.environ.get("GITHUB_STEP_SUMMARY")

    @staticmethod
    def get_path_file() -> Optional[str]:
        """Get GitHub PATH file path."""
        return os.environ.get("GITHUB_PATH")

    @staticmethod
    def get_run_id() -> str:
        """Get GitHub run ID."""
        return os.environ.get("GITHUB_RUN_ID", "N/A")

    @staticmethod
    def write_output(key: str, value: Any) -> None:
        """Write output variable for GitHub Actions."""
        output_file = GitHubActions.get_output_file()
        if output_file:
            with open(output_file, "a") as f:
                f.write(f"{key}={value}\n")

    @staticmethod
    def write_outputs(outputs: Dict[str, Any]) -> None:
        """Write multiple output variables."""
        output_file = GitHubActions.get_output_file()
        if output_file:
            with open(output_file, "a") as f:
                for key, value in outputs.items():
                    f.write(f"{key}={value}\n")

    @staticmethod
    def append_to_path(path: str) -> None:
        """Add path to GitHub Actions PATH."""
        path_file = GitHubActions.get_path_file()
        if path_file:
            with open(path_file, "a") as f:
                f.write(f"{path}\n")


class ReportParser:
    """JSON report parsing utilities."""

    @staticmethod
    def load_report(report_path: str) -> Optional[Dict[str, Any]]:
        """Load and parse JSON report file."""
        if not report_path or not Path(report_path).exists():
            Logger.error(f"Report file not found: {report_path}")
            return None

        try:
            with open(report_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            Logger.error(f"Failed to parse JSON report: {e}")
            return None
        except Exception as e:
            Logger.error(f"Failed to read report file: {e}")
            return None

    @staticmethod
    def extract_issues(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract failed URLs/issues from various JSON formats."""
        issues = []

        # Try current format (.issues[]) - works for all format versions
        if "issues" in data:
            for issue in data["issues"]:
                issues.append({
                    "file": issue.get("file", ""),
                    "line": issue.get("line", 1),
                    "url": issue.get("url", ""),
                    "status_code": issue.get("status_code"),
                    "error": issue.get("description") or issue.get("error"),
                })

        # Try older format (.failed_urls[])
        elif "failed_urls" in data:
            for item in data["failed_urls"]:
                issues.append({
                    "file": item.get("file", ""),
                    "line": item.get("line", 1),
                    "url": item.get("url", ""),
                    "status_code": item.get("status_code"),
                    "error": item.get("error"),
                })

        # Try alternative older JSON structure (.results[])
        elif "results" in data:
            for result in data["results"]:
                success = result.get("success")
                if success is False or (result.get("result", {}).get("success") is False):
                    location = result.get("location", {})
                    result_data = result.get("result", {})

                    issues.append({
                        "file": location.get("file") or result.get("file", ""),
                        "line": location.get("line") or result.get("line", 1),
                        "url": result.get("url", ""),
                        "status_code": result_data.get("status_code") or result.get("status_code"),
                        "error": result_data.get("error") or result.get("error"),
                    })

        return issues

    @staticmethod
    def extract_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from JSON report."""
        status = data.get("status", "unknown")
        broken_urls = len(ReportParser.extract_issues(data))

        # Try rich format with detailed metadata
        if "urls" in data and isinstance(data["urls"], dict):
            urls_data = data["urls"]
            total_urls = urls_data.get("validated", urls_data.get("unique", 0))
            success_rate = int(urls_data.get("success_rate", 0))

            # Additional metadata
            files_data = data.get("files", {})
            return {
                "total_urls": total_urls,
                "broken_urls": broken_urls,
                "success_rate": success_rate,
                "status": status,
                "total_files": files_data.get("total", 0),
                "processed_files": files_data.get("processed", 0),
                "total_found_urls": urls_data.get("total_found", 0),
                "unique_urls": urls_data.get("unique", 0),
            }
        else:
            # Fallback to basic format
            if status == "success":
                total_urls = max(1, broken_urls)
            else:
                total_urls = max(broken_urls, 1)

            success_rate = 0
            if total_urls > 0:
                success_rate = (total_urls - broken_urls) * 100 // total_urls

            return {
                "total_urls": total_urls,
                "broken_urls": broken_urls,
                "success_rate": success_rate,
                "status": status,
                "total_files": 0,
                "processed_files": 0,
                "total_found_urls": 0,
                "unique_urls": 0,
            }


class PathUtils:
    """File path utilities."""

    @staticmethod
    def normalize_file_path(file_path: str) -> str:
        """Clean and normalize file path for display."""
        try:
            normalized = Path(file_path)
            parts = []
            for part in normalized.parts:
                if part == "..":
                    if parts:
                        parts.pop()
                elif part not in (".", ""):
                    parts.append(part)

            if parts:
                clean_file = "/".join(parts)
            else:
                clean_file = Path(file_path).name

            return clean_file.lstrip("./")
        except Exception:
            return str(Path(file_path)).lstrip("./")


class ValidationUtils:
    """Common validation utilities."""

    @staticmethod
    def to_bool(value: Any) -> bool:
        """Convert string input to boolean."""
        if not value:
            return False
        lower_value = str(value).lower()
        return lower_value in ("true", "1", "yes", "on")

    @staticmethod
    def escape_markdown(text: Any) -> str:
        """Escape text for safe inclusion in markdown."""
        return str(text).replace("|", "\\|").replace("\n", " ").replace("\r", " ")