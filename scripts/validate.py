#!/usr/bin/env python3
"""Validation script for urlsup - builds command arguments and executes URL validation."""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

from common import (
    GitHubActions,
    Logger,
    ParallelProcessor,
    ReportParser,
    Telemetry,
    ValidationUtils,
)


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


def run_urlsup_batch(file_batch: List[str], batch_id: int) -> str:
    """Run urlsup on a batch of files and return the report path."""
    import subprocess
    import tempfile

    # Create unique report file for this batch
    workspace = GitHubActions.get_workspace()
    report_file = Path(workspace) / f"urlsup-report-batch-{batch_id}.json"

    # Build command for this batch
    cmd_args = build_command()

    # Replace the files argument with our batch
    # Remove any existing file arguments and add our batch
    filtered_args = []
    skip_next = False

    for i, arg in enumerate(cmd_args):
        if skip_next:
            skip_next = False
            continue
        if arg in file_batch or (i == 0 and arg == "."):
            # Skip file arguments, we'll add our batch
            continue
        filtered_args.append(arg)

    # Add our specific batch files
    batch_cmd = ["urlsup"] + file_batch + filtered_args

    Logger.info(f"Batch {batch_id}: Processing {len(file_batch)} files")

    try:
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False
        ) as temp_stdout, tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_stderr:

            result = subprocess.run(batch_cmd, stdout=temp_stdout, stderr=temp_stderr, text=True)

            # Copy stdout to report file
            temp_stdout.seek(0)
            with open(report_file, "w") as f:
                f.write(temp_stdout.read())

            # Log any errors
            if result.returncode != 0:
                temp_stderr.seek(0)
                stderr_content = temp_stderr.read()
                if stderr_content.strip():
                    Logger.warning(f"Batch {batch_id} stderr: {stderr_content}")

    except Exception as e:
        Logger.error(f"Batch {batch_id} failed: {e}")
        # Create empty report for this batch
        with open(report_file, "w") as f:
            json.dump({"status": "failure", "issues": []}, f)

    finally:
        # Clean up temp files
        try:
            os.unlink(temp_stdout.name)
            os.unlink(temp_stderr.name)
        except Exception:
            pass

    return str(report_file)


def validate_urls_parallel() -> None:
    """Validate URLs using parallel processing."""
    Logger.info("Starting parallel URL validation...")

    # Start telemetry
    Telemetry.start_timer("validation")
    Telemetry.start_timer("file_discovery")

    # Discover all files that need processing
    files_to_process = ParallelProcessor.discover_files()
    file_discovery_time = Telemetry.end_timer("file_discovery")

    Logger.info(f"Discovered {len(files_to_process)} files for validation")
    Telemetry.record_metric("discovered_files", len(files_to_process))

    if not files_to_process:
        Logger.warning("No files found for validation")
        # Create empty report
        report_file = Path(GitHubActions.get_workspace()) / "urlsup-report.json"
        with open(report_file, "w") as f:
            json.dump(
                {
                    "status": "success",
                    "issues": [],
                    "urls": {"validated": 0, "unique": 0},
                    "files": {"total": 0, "processed": 0},
                },
                f,
            )
        return

    # Split files into batches
    batch_size = ParallelProcessor.get_optimal_batch_size()
    batches = ParallelProcessor.split_files_into_batches(files_to_process, batch_size)

    Logger.info(f"Processing {len(batches)} batches with up to {batch_size} workers")
    Telemetry.record_metric("batch_count", len(batches))
    Telemetry.record_metric("batch_size", batch_size)

    # Process batches in parallel
    Telemetry.start_timer("parallel_processing")
    report_paths = []

    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        # Submit all batch jobs
        future_to_batch = {
            executor.submit(run_urlsup_batch, batch, i): i for i, batch in enumerate(batches)
        }

        # Collect results as they complete
        for future in as_completed(future_to_batch):
            batch_id = future_to_batch[future]
            try:
                report_path = future.result()
                report_paths.append(report_path)
                Logger.info(f"Batch {batch_id} completed: {report_path}")
            except Exception as e:
                Logger.error(f"Batch {batch_id} failed with exception: {e}")

    parallel_processing_time = Telemetry.end_timer("parallel_processing")
    Logger.info(f"Parallel processing completed in {parallel_processing_time:.2f}s")

    # Merge all reports
    Telemetry.start_timer("report_merging")
    merged_report = ParallelProcessor.merge_reports(report_paths)
    report_merging_time = Telemetry.end_timer("report_merging")

    # Write merged report
    final_report_path = Path(GitHubActions.get_workspace()) / "urlsup-report.json"
    with open(final_report_path, "w") as f:
        json.dump(merged_report, f, indent=2)

    Logger.info(f"Merged report written to: {final_report_path}")
    Logger.info(f"Total issues found: {len(merged_report.get('issues', []))}")

    # Clean up batch reports
    for report_path in report_paths:
        try:
            os.unlink(report_path)
        except Exception:
            pass

    # Record performance metrics
    Telemetry.record_metric("file_discovery_time", file_discovery_time)
    Telemetry.record_metric("parallel_processing_time", parallel_processing_time)
    Telemetry.record_metric("report_merging_time", report_merging_time)


def validate_urls() -> None:
    """Validate URLs using urlsup."""
    Logger.info("Starting URL validation...")

    # Start telemetry collection
    Telemetry.start_timer("validation")
    Telemetry.record_metric("action_version", "2.0.0")

    # Record setup telemetry from environment
    setup_duration = os.environ.get("SETUP_DURATION", "0")
    cache_hit = os.environ.get("CACHE_HIT", "false").lower() == "true"
    try:
        Telemetry.record_metric("setup_duration", float(setup_duration))
    except ValueError:
        Telemetry.record_metric("setup_duration", 0.0)
    Telemetry.record_metric("cache_hit", cache_hit)

    # Check if we should use parallel processing
    if ParallelProcessor.should_use_parallel_processing():
        Logger.info("🚀 Using parallel processing for better performance")
        Telemetry.record_metric("processing_mode", "parallel")
        validate_urls_parallel()

        # Continue with telemetry and output processing
        validation_duration = Telemetry.end_timer("validation")
        Telemetry.record_metric("validation_duration", validation_duration)
        Telemetry.create_telemetry_annotations()

        # Parse the merged results
        report_file = Path(GitHubActions.get_workspace()) / "urlsup-report.json"
        parse_results(report_file)
        GitHubActions.write_output("exit-code", 0)

        return

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

    # Record telemetry about repository
    workspace = GitHubActions.get_workspace()
    file_count = len(list(Path(workspace).rglob("*"))) if workspace else 0
    Telemetry.record_metric("total_files", file_count)

    # Create report file
    report_file = Path(GitHubActions.get_workspace()) / "urlsup-report.json"

    # Log the command that will be executed (for debugging)
    Logger.info(f"Executing: urlsup {' '.join(cmd_args)}")

    # Execute urlsup and capture exit code
    exit_code = 0
    Telemetry.start_timer("urlsup_execution")
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False
        ) as temp_stdout, tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_stderr:
            result = subprocess.run(
                ["urlsup"] + cmd_args, stdout=temp_stdout, stderr=temp_stderr, text=True
            )
            exit_code = result.returncode

            # Record execution telemetry
            execution_duration = Telemetry.end_timer("urlsup_execution")
            Telemetry.record_metric("urlsup_execution_duration", execution_duration)
            Telemetry.record_metric("urlsup_exit_code", exit_code)

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

    # End validation timer and create telemetry
    validation_duration = Telemetry.end_timer("validation")
    Telemetry.record_metric("validation_duration", validation_duration)

    # Record final metrics
    github_output = GitHubActions.get_output_file()
    if github_output and Path(github_output).exists():
        try:
            with open(github_output) as f:
                for line in f:
                    if line.startswith("total-urls="):
                        Telemetry.record_metric(
                            "total_urls_validated", int(line.split("=", 1)[1].strip())
                        )
                    elif line.startswith("broken-urls="):
                        Telemetry.record_metric(
                            "broken_urls_found", int(line.split("=", 1)[1].strip())
                        )
        except (ValueError, IndexError):
            pass

    # Create telemetry annotations
    Telemetry.create_telemetry_annotations()

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
