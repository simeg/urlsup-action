#!/usr/bin/env python3
"""Validation script for urlsup - builds command arguments and executes URL validation."""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

from common import GitHubActions, Logger, ReportParser, ValidationUtils


def build_command() -> List[str]:
    """Build urlsup command arguments from environment variables."""
    cmd_args = []

    # File selection
    files = os.environ.get("INPUT_FILES", "")
    if files:
        # Split files by space and add each as separate argument
        cmd_args.extend(files.split())
    else:
        cmd_args.append(".")

    # Recursive processing
    if ValidationUtils.to_bool(os.environ.get("INPUT_RECURSIVE", "true")):
        cmd_args.append("--recursive")

    # Include extensions
    include_extensions = os.environ.get("INPUT_INCLUDE_EXTENSIONS")
    if include_extensions:
        cmd_args.extend(["--include", include_extensions])

    # Network configuration
    timeout = os.environ.get("INPUT_TIMEOUT")
    if timeout:
        cmd_args.extend(["--timeout", timeout])

    concurrency = os.environ.get("INPUT_CONCURRENCY")
    if concurrency:
        cmd_args.extend(["--concurrency", concurrency])

    retry = os.environ.get("INPUT_RETRY")
    if retry and retry != "0":
        cmd_args.extend(["--retry", retry])

    retry_delay = os.environ.get("INPUT_RETRY_DELAY")
    if retry_delay:
        cmd_args.extend(["--retry-delay", retry_delay])

    rate_limit = os.environ.get("INPUT_RATE_LIMIT")
    if rate_limit and rate_limit != "0":
        cmd_args.extend(["--rate-limit", rate_limit])

    # URL filtering
    allowlist = os.environ.get("INPUT_ALLOWLIST")
    if allowlist:
        cmd_args.extend(["--allowlist", allowlist])

    allow_status = os.environ.get("INPUT_ALLOW_STATUS")
    if allow_status:
        cmd_args.extend(["--allow-status", allow_status])

    exclude_pattern = os.environ.get("INPUT_EXCLUDE_PATTERN")
    if exclude_pattern:
        cmd_args.extend(["--exclude-pattern", exclude_pattern])

    if ValidationUtils.to_bool(os.environ.get("INPUT_ALLOW_TIMEOUT", "false")):
        cmd_args.append("--allow-timeout")

    failure_threshold = os.environ.get("INPUT_FAILURE_THRESHOLD")
    if failure_threshold:
        cmd_args.extend(["--failure-threshold", failure_threshold])

    # Output configuration
    cmd_args.extend(["--format", "json"])

    if ValidationUtils.to_bool(os.environ.get("INPUT_QUIET", "false")):
        cmd_args.append("--quiet")

    if ValidationUtils.to_bool(os.environ.get("INPUT_VERBOSE", "false")):
        cmd_args.append("--verbose")

    # Progress bar control (always disable in CI)
    cmd_args.append("--no-progress")

    # Advanced options
    user_agent = os.environ.get("INPUT_USER_AGENT")
    if user_agent:
        cmd_args.extend(["--user-agent", user_agent])

    proxy = os.environ.get("INPUT_PROXY")
    if proxy:
        cmd_args.extend(["--proxy", proxy])

    if ValidationUtils.to_bool(os.environ.get("INPUT_INSECURE", "false")):
        cmd_args.append("--insecure")

    # Configuration file options
    config = os.environ.get("INPUT_CONFIG")
    if config:
        cmd_args.extend(["--config", config])

    if ValidationUtils.to_bool(os.environ.get("INPUT_NO_CONFIG", "false")):
        cmd_args.append("--no-config")

    return cmd_args


def parse_results(json_file: Path) -> bool:
    """Parse JSON output and extract metrics."""
    if not json_file.exists():
        Logger.error(f"JSON report file not found: {json_file}")
        GitHubActions.write_outputs(
            {
                "total-urls": 0,
                "broken-urls": 0,
                "success-rate": "0%",
                "report-path": "",
            }
        )
        return False

    data = ReportParser.load_report(str(json_file))
    if not data:
        Logger.warning("File does not contain valid JSON, attempting basic parsing")
        parse_non_json(json_file)
        return True

    # Extract metrics using shared parser
    metrics = ReportParser.extract_metrics(data)

    # Write outputs
    outputs = {
        "total-urls": metrics["total_urls"],
        "broken-urls": metrics["broken_urls"],
        "success-rate": f"{metrics['success_rate']}%",
        "report-path": str(json_file),
        "total-files": metrics["total_files"],
        "processed-files": metrics["processed_files"],
        "total-found-urls": metrics["total_found_urls"],
        "unique-urls": metrics["unique_urls"],
        "status": metrics["status"],
    }
    GitHubActions.write_outputs(outputs)
    return True


def parse_non_json(file_path: Path) -> None:
    """Parse non-JSON output (fallback)."""
    Logger.warning("Attempting to parse non-JSON output")

    total_urls = 0
    broken_urls = 0

    try:
        with open(file_path) as f:
            content = f.read()

        # Look for common patterns in text output
        urls_found_match = re.search(r"(\d+) URLs found", content)
        if urls_found_match:
            total_urls = int(urls_found_match.group(1))

        failed_match = re.search(r"(\d+) failed", content)
        if failed_match:
            broken_urls = int(failed_match.group(1))

    except Exception as e:
        Logger.warning(f"Failed to parse non-JSON output: {e}")

    success_rate = 0
    if total_urls > 0:
        success_rate = (total_urls - broken_urls) * 100 // total_urls

    GitHubActions.write_outputs(
        {
            "total-urls": total_urls,
            "broken-urls": broken_urls,
            "success-rate": f"{success_rate}%",
        }
    )


def validate_urls() -> None:
    """Validate URLs using urlsup."""
    Logger.info("Starting URL validation...")

    # Check if urlsup is available
    try:
        subprocess.run(["urlsup", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        Logger.error("❌ urlsup binary not found in PATH")
        Logger.error(
            "This usually means the setup step failed or urlsup wasn't installed properly."
        )
        Logger.error("")
        Logger.error("To fix this issue:")
        Logger.error("1. Ensure you're using actions/checkout@v4 before this action")
        Logger.error("2. Check that the action downloaded urlsup successfully")
        Logger.error("3. Verify your runner has internet access to download binaries")
        Logger.error("")
        Logger.error(f"Technical details: {e}")
        Logger.error(f"Current PATH: {os.environ.get('PATH', 'Not set')}")
        GitHubActions.write_outputs(
            {
                "total-urls": 0,
                "broken-urls": 0,
                "success-rate": "0%",
                "exit-code": 127,
                "report-path": "",
            }
        )
        sys.exit(127)

    # Build command arguments
    cmd_args = build_command()

    # Create report file
    report_file = Path(GitHubActions.get_workspace()) / "urlsup-report.json"

    # Log the command that will be executed (for debugging)
    Logger.info(f"Executing: urlsup {' '.join(cmd_args)}")

    # Execute urlsup and capture exit code
    exit_code = 0
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False
        ) as temp_stdout, tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_stderr:
            result = subprocess.run(
                ["urlsup"] + cmd_args, stdout=temp_stdout, stderr=temp_stderr, text=True
            )
            exit_code = result.returncode

            if exit_code != 0:
                Logger.warning(f"urlsup exited with code {exit_code}")

            # Show stderr if there were issues
            temp_stderr.seek(0)
            stderr_content = temp_stderr.read()
            if stderr_content.strip():
                Logger.info("urlsup stderr output:")
                print(stderr_content, file=sys.stderr)

            # Copy stdout to report file
            temp_stdout.seek(0)
            with open(report_file, "w") as f:
                f.write(temp_stdout.read())

    except Exception as e:
        Logger.error("❌ Failed to execute urlsup command")
        Logger.error(f"Error: {e}")
        Logger.error("")
        Logger.error("Common causes:")
        Logger.error("- Network connectivity issues")
        Logger.error("- Invalid command arguments")
        Logger.error("- Insufficient disk space for reports")
        Logger.error("- Permission issues with file access")
        Logger.error("")
        Logger.error(f"Command attempted: urlsup {' '.join(cmd_args)}")
        exit_code = 1
    finally:
        # Clean up temp files
        try:
            os.unlink(temp_stdout.name)
            os.unlink(temp_stderr.name)
        except Exception:
            pass

    # Debug: show first few lines of the output
    Logger.info("Report file preview:")
    try:
        with open(report_file) as f:
            lines = f.readlines()[:5]
            for line in lines:
                print(line.rstrip(), file=sys.stderr)
    except Exception:
        pass

    # Parse results
    parse_results(report_file)

    GitHubActions.write_output("exit-code", exit_code)

    # Determine if we should fail the action
    fail_on_error = ValidationUtils.to_bool(os.environ.get("INPUT_FAIL_ON_ERROR", "true"))

    # Get the number of broken URLs from the parsed results
    broken_urls_count = 0
    github_output = GitHubActions.get_output_file()
    if github_output and Path(github_output).exists():
        try:
            with open(github_output) as f:
                for line in f:
                    if line.startswith("broken-urls="):
                        broken_urls_count = int(line.split("=", 1)[1].strip())
                        break
        except (ValueError, IndexError):
            # Fallback: check JSON directly
            data = ReportParser.load_report(str(report_file))
            if data:
                broken_urls_count = len(ReportParser.extract_issues(data))

    Logger.info(f"Detected {broken_urls_count} broken URLs, fail_on_error={fail_on_error}")

    # Log the results but never exit with error code during validation
    # The action will handle failing the workflow in a separate step
    if broken_urls_count > 0:
        if fail_on_error:
            Logger.error(f"URL validation failed with {broken_urls_count} broken URLs")
        else:
            Logger.warning(
                f"URL validation found {broken_urls_count} broken URLs, "
                f"but fail-on-error is disabled"
            )
    else:
        Logger.success("All URLs are valid!")

    # Always exit successfully to ensure annotations and summary are generated
    # The workflow failure will be handled by the action's final step


if __name__ == "__main__":
    validate_urls()
