#!/usr/bin/env python3
"""Common utilities and shared functionality for urlsup-action scripts."""

import json
import os
import sys
import time
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
        """Write multiple output variables efficiently in a single operation."""
        output_file = GitHubActions.get_output_file()
        if output_file:
            # Build output string in memory then write once for better performance
            output_lines = [f"{key}={value}" for key, value in outputs.items()]
            output_content = "\n".join(output_lines) + "\n"

            with open(output_file, "a", encoding="utf-8") as f:
                f.write(output_content)

    @staticmethod
    def append_to_path(path: str) -> None:
        """Add path to GitHub Actions PATH."""
        path_file = GitHubActions.get_path_file()
        if path_file:
            with open(path_file, "a") as f:
                f.write(f"{path}\n")


class ReportParser:
    """JSON report parsing utilities with caching for performance."""

    _cached_reports = {}  # Simple cache for report data

    @staticmethod
    def load_report(report_path: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Load and parse JSON report file with optional caching."""
        if not report_path or not Path(report_path).exists():
            Logger.error(f"Report file not found: {report_path}")
            return None

        # Check cache first for performance
        if use_cache and report_path in ReportParser._cached_reports:
            return ReportParser._cached_reports[report_path]

        try:
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Cache the parsed data for reuse
            if use_cache:
                ReportParser._cached_reports[report_path] = data

            return data
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
                issues.append(
                    {
                        "file": issue.get("file", ""),
                        "line": issue.get("line", 1),
                        "url": issue.get("url", ""),
                        "status_code": issue.get("status_code"),
                        "error": issue.get("description") or issue.get("error"),
                    }
                )

        # Try older format (.failed_urls[])
        elif "failed_urls" in data:
            for item in data["failed_urls"]:
                issues.append(
                    {
                        "file": item.get("file", ""),
                        "line": item.get("line", 1),
                        "url": item.get("url", ""),
                        "status_code": item.get("status_code"),
                        "error": item.get("error"),
                    }
                )

        # Try alternative older JSON structure (.results[])
        elif "results" in data:
            for result in data["results"]:
                success = result.get("success")
                if success is False or (result.get("result", {}).get("success") is False):
                    location = result.get("location", {})
                    result_data = result.get("result", {})

                    issues.append(
                        {
                            "file": location.get("file") or result.get("file", ""),
                            "line": location.get("line") or result.get("line", 1),
                            "url": result.get("url", ""),
                            "status_code": result_data.get("status_code")
                            or result.get("status_code"),
                            "error": result_data.get("error") or result.get("error"),
                        }
                    )

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


class Telemetry:
    """Telemetry collection utilities for performance insights."""

    _start_time = None
    _metrics = {}

    @staticmethod
    def is_enabled() -> bool:
        """Check if telemetry is enabled."""
        return ValidationUtils.to_bool(os.environ.get("INPUT_TELEMETRY", "true"))

    @staticmethod
    def start_timer(name: str) -> None:
        """Start a named timer."""
        if Telemetry.is_enabled():
            Telemetry._metrics[f"{name}_start"] = time.time()

    @staticmethod
    def end_timer(name: str) -> float:
        """End a named timer and return duration."""
        if not Telemetry.is_enabled():
            return 0.0

        start_key = f"{name}_start"
        if start_key in Telemetry._metrics:
            duration = time.time() - Telemetry._metrics[start_key]
            Telemetry._metrics[f"{name}_duration"] = duration
            return duration
        return 0.0

    @staticmethod
    def record_metric(name: str, value: Any) -> None:
        """Record a named metric."""
        if Telemetry.is_enabled():
            Telemetry._metrics[name] = value

    @staticmethod
    def get_repository_info() -> Dict[str, str]:
        """Get anonymized repository information."""
        if not Telemetry.is_enabled():
            return {}

        repo = os.environ.get("GITHUB_REPOSITORY", "unknown")
        # Only collect non-sensitive info
        return {
            "repo_type": "public" if repo != "unknown" else "unknown",
            "runner_os": os.environ.get("RUNNER_OS", "unknown"),
            "action_version": "2.0.0",
        }

    @staticmethod
    def create_telemetry_annotations() -> None:
        """Create GitHub annotations with telemetry data."""
        if not Telemetry.is_enabled():
            return

        metrics = Telemetry._metrics

        # Create telemetry annotations that show up in GitHub UI
        validation_duration = metrics.get("validation_duration", 0)
        if validation_duration > 0:
            print(f"::notice title=Performance::Validation completed in {validation_duration:.2f}s")

        setup_duration = metrics.get("setup_duration", 0)
        if setup_duration > 0:
            print(f"::notice title=Performance::Setup completed in {setup_duration:.2f}s")

        cache_hit = metrics.get("cache_hit", False)
        if cache_hit:
            print("::notice title=Performance::Binary cache hit - faster execution")

        # Repository size metrics
        total_files = metrics.get("total_files", 0)
        if total_files > 0:
            if total_files > 100:
                size_category = "large"
            elif total_files > 20:
                size_category = "medium"
            else:
                size_category = "small"
            print(
                f"::notice title=Repository::Size category: {size_category} ({total_files} files)"
            )

    @staticmethod
    def create_summary_metrics() -> str:
        """Create telemetry summary for job summaries."""
        if not Telemetry.is_enabled():
            return ""

        metrics = Telemetry._metrics

        summary_lines = ["## 📊 Performance Metrics", ""]

        # Timing metrics
        validation_duration = metrics.get("validation_duration", 0)
        setup_duration = metrics.get("setup_duration", 0)

        if validation_duration > 0 or setup_duration > 0:
            summary_lines.append("| Metric | Value |")
            summary_lines.append("|--------|-------|")

            if setup_duration > 0:
                summary_lines.append(f"| Setup Time | {setup_duration:.2f}s |")
            if validation_duration > 0:
                summary_lines.append(f"| Validation Time | {validation_duration:.2f}s |")

            cache_hit = metrics.get("cache_hit", False)
            summary_lines.append(f"| Cache Status | {'✅ Hit' if cache_hit else '❌ Miss'} |")

            # Performance insights
            summary_lines.append("")
            if validation_duration > 10:
                summary_lines.append(
                    "💡 **Performance Tip**: Consider increasing concurrency"
                    " or excluding slow domains"
                )
            elif validation_duration < 5:
                summary_lines.append("⚡ **Great Performance**: Validation completed quickly!")

        return "\n".join(summary_lines) if summary_lines else ""


class ParallelProcessor:
    """Utilities for parallel file processing."""

    @staticmethod
    def should_use_parallel_processing() -> bool:
        """Determine if parallel processing should be used."""
        # Check if parallel processing is enabled
        parallel_enabled = ValidationUtils.to_bool(
            os.environ.get("INPUT_PARALLEL_PROCESSING", "false")
        )
        if not parallel_enabled:
            return False

        # Only use parallel processing for larger workloads
        files_input = os.environ.get("INPUT_FILES", ".")
        file_paths = files_input.split() if files_input.strip() else ["."]

        # Count total files that would be processed
        total_files = 0
        workspace = GitHubActions.get_workspace()

        for file_path in file_paths:
            full_path = Path(workspace) / file_path if workspace else Path(file_path)
            if full_path.is_file():
                total_files += 1
            elif full_path.is_dir():
                # Estimate files in directory (simple heuristic)
                try:
                    total_files += len(list(full_path.rglob("*")))
                except Exception:
                    total_files += 50  # Fallback estimate

        # Use parallel processing for repositories with many files
        return total_files >= 20

    @staticmethod
    def get_optimal_batch_size() -> int:
        """Calculate optimal batch size for parallel processing."""
        # Get system info
        import multiprocessing

        cpu_count = multiprocessing.cpu_count()

        # Get concurrency setting from action inputs
        concurrency = os.environ.get("INPUT_CONCURRENCY")
        if concurrency and concurrency.isdigit():
            requested_workers = int(concurrency)
            # Cap at reasonable limits for file processing
            max_workers = min(requested_workers, cpu_count, 4)  # Conservative cap at 4
        else:
            max_workers = min(4, cpu_count)  # Conservative default

        # Batch size should allow for efficient work distribution
        return max(1, max_workers)

    @staticmethod
    def split_files_into_batches(file_paths: List[str], batch_size: int) -> List[List[str]]:
        """Split file paths into batches for parallel processing."""
        if not file_paths or batch_size <= 1:
            return [file_paths]

        batches = []
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i : i + batch_size]
            batches.append(batch)

        return batches

    @staticmethod
    def discover_files() -> List[str]:
        """Discover files that would be processed by urlsup."""
        files_input = os.environ.get("INPUT_FILES", ".")
        include_extensions = os.environ.get("INPUT_INCLUDE_EXTENSIONS", "md,rst,txt,html")
        recursive = ValidationUtils.to_bool(os.environ.get("INPUT_RECURSIVE", "true"))
        workspace = GitHubActions.get_workspace()

        file_paths = files_input.split() if files_input.strip() else ["."]
        discovered_files = []

        # Convert extensions to set for faster lookup
        extensions = {ext.strip().lower() for ext in include_extensions.split(",")}

        for file_path in file_paths:
            full_path = Path(workspace) / file_path if workspace else Path(file_path)

            if full_path.is_file():
                # Check if file has the right extension
                file_ext = full_path.suffix.lstrip(".").lower()
                if extensions and file_ext in extensions:
                    discovered_files.append(str(full_path))
            elif full_path.is_dir() and recursive:
                # Find files in directory
                for ext in extensions:
                    pattern = f"**/*.{ext}" if recursive else f"*.{ext}"
                    discovered_files.extend(str(f) for f in full_path.glob(pattern))

        return discovered_files

    @staticmethod
    def merge_reports(report_paths: List[str]) -> Dict[str, Any]:
        """Merge multiple JSON reports into a single report."""
        merged_report = {
            "status": "success",
            "issues": [],
            "urls": {"total_found": 0, "unique": 0, "validated": 0, "success_rate": 0},
            "files": {"total": 0, "processed": 0},
        }

        all_issues = []
        all_urls = set()
        total_validated = 0
        total_files = 0
        processed_files = 0

        for report_path in report_paths:
            if not Path(report_path).exists():
                continue

            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    report = json.load(f)

                # Merge issues
                if "issues" in report:
                    all_issues.extend(report["issues"])

                # Track URLs
                if "urls" in report:
                    url_data = report["urls"]
                    total_validated += url_data.get("validated", 0)
                    # Note: We can't easily merge unique URLs without the actual URL list

                # Track files
                if "files" in report:
                    file_data = report["files"]
                    total_files += file_data.get("total", 0)
                    processed_files += file_data.get("processed", 0)

                # If any report failed, mark merged report as failed
                if report.get("status") == "failure":
                    merged_report["status"] = "failure"

            except Exception as e:
                Logger.warning(f"Failed to merge report {report_path}: {e}")
                continue

        # Update merged report
        merged_report["issues"] = all_issues
        merged_report["urls"]["validated"] = total_validated
        merged_report["urls"]["unique"] = len(all_urls) if all_urls else total_validated
        merged_report["files"]["total"] = total_files
        merged_report["files"]["processed"] = processed_files

        # Calculate success rate
        if total_validated > 0:
            success_rate = ((total_validated - len(all_issues)) / total_validated) * 100
            merged_report["urls"]["success_rate"] = int(success_rate)

        return merged_report
