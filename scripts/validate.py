#!/usr/bin/env python3
"""
Validation script for urlsup - builds command arguments and executes URL validation.
"""

import os
import sys
import json
import subprocess
import tempfile
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


def to_bool(value):
    """Convert string input to boolean."""
    if not value:
        return False
    lower_value = str(value).lower()
    return lower_value in ("true", "1", "yes", "on")


def build_command():
    """Build urlsup command arguments from environment variables."""
    cmd_args = []
    
    # File selection
    files = os.environ.get('INPUT_FILES', '')
    if files:
        # Split files by space and add each as separate argument
        cmd_args.extend(files.split())
    else:
        cmd_args.append('.')
    
    # Recursive processing
    if to_bool(os.environ.get('INPUT_RECURSIVE', 'true')):
        cmd_args.append('--recursive')
    
    # Include extensions
    include_extensions = os.environ.get('INPUT_INCLUDE_EXTENSIONS')
    if include_extensions:
        cmd_args.extend(['--include', include_extensions])
    
    # Network configuration
    timeout = os.environ.get('INPUT_TIMEOUT')
    if timeout:
        cmd_args.extend(['--timeout', timeout])
    
    concurrency = os.environ.get('INPUT_CONCURRENCY')
    if concurrency:
        cmd_args.extend(['--concurrency', concurrency])
    
    retry = os.environ.get('INPUT_RETRY')
    if retry and retry != "0":
        cmd_args.extend(['--retry', retry])
    
    retry_delay = os.environ.get('INPUT_RETRY_DELAY')
    if retry_delay:
        cmd_args.extend(['--retry-delay', retry_delay])
    
    rate_limit = os.environ.get('INPUT_RATE_LIMIT')
    if rate_limit and rate_limit != "0":
        cmd_args.extend(['--rate-limit', rate_limit])
    
    # URL filtering
    allowlist = os.environ.get('INPUT_ALLOWLIST')
    if allowlist:
        cmd_args.extend(['--allowlist', allowlist])
    
    allow_status = os.environ.get('INPUT_ALLOW_STATUS')
    if allow_status:
        cmd_args.extend(['--allow-status', allow_status])
    
    exclude_pattern = os.environ.get('INPUT_EXCLUDE_PATTERN')
    if exclude_pattern:
        cmd_args.extend(['--exclude-pattern', exclude_pattern])
    
    if to_bool(os.environ.get('INPUT_ALLOW_TIMEOUT', 'false')):
        cmd_args.append('--allow-timeout')
    
    failure_threshold = os.environ.get('INPUT_FAILURE_THRESHOLD')
    if failure_threshold:
        cmd_args.extend(['--failure-threshold', failure_threshold])
    
    # Output configuration
    cmd_args.extend(['--format', 'json'])
    
    if to_bool(os.environ.get('INPUT_QUIET', 'false')):
        cmd_args.append('--quiet')
    
    if to_bool(os.environ.get('INPUT_VERBOSE', 'false')):
        cmd_args.append('--verbose')
    
    # Progress bar control (always disable in CI)
    cmd_args.append('--no-progress')
    
    # Advanced options
    user_agent = os.environ.get('INPUT_USER_AGENT')
    if user_agent:
        cmd_args.extend(['--user-agent', user_agent])
    
    proxy = os.environ.get('INPUT_PROXY')
    if proxy:
        cmd_args.extend(['--proxy', proxy])
    
    if to_bool(os.environ.get('INPUT_INSECURE', 'false')):
        cmd_args.append('--insecure')
    
    # Configuration file options
    config = os.environ.get('INPUT_CONFIG')
    if config:
        cmd_args.extend(['--config', config])
    
    if to_bool(os.environ.get('INPUT_NO_CONFIG', 'false')):
        cmd_args.append('--no-config')
    
    return cmd_args


def parse_results(json_file):
    """Parse JSON output and extract metrics."""
    github_output = os.environ.get('GITHUB_OUTPUT')
    
    if not json_file.exists():
        log_error(f"JSON report file not found: {json_file}")
        if github_output:
            with open(github_output, 'a') as f:
                f.write("total-urls=0\n")
                f.write("broken-urls=0\n")
                f.write("success-rate=0%\n")
                f.write("report-path=\n")
        return False
    
    try:
        with open(json_file) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        log_warning("File does not contain valid JSON, attempting basic parsing")
        parse_non_json(json_file)
        return True
    
    # Extract metrics using urlsup v2.2.0 format
    status = data.get('status', 'unknown')
    broken_urls = len(data.get('issues', []))
    
    # urlsup v2.2.0 doesn't report total URLs in JSON, so we estimate
    if status == "success":
        # If successful, there are some URLs (unknown count) with 0 broken
        total_urls = 1  # Placeholder, at least 1 URL was checked
    else:
        # If failure, we only know the broken count
        total_urls = broken_urls
    
    success_rate = 0
    if total_urls > 0:
        success_rate = (total_urls - broken_urls) * 100 // total_urls
    
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"total-urls={total_urls}\n")
            f.write(f"broken-urls={broken_urls}\n")
            f.write(f"success-rate={success_rate}%\n")
            f.write(f"report-path={json_file}\n")
    
    return True


def parse_non_json(file_path):
    """Parse non-JSON output (fallback)."""
    log_warning("Attempting to parse non-JSON output")
    
    total_urls = 0
    broken_urls = 0
    
    try:
        with open(file_path) as f:
            content = f.read()
        
        # Look for common patterns in text output
        import re
        
        # Try to extract numbers from common urlsup output patterns
        urls_found_match = re.search(r'(\d+) URLs found', content)
        if urls_found_match:
            total_urls = int(urls_found_match.group(1))
        
        failed_match = re.search(r'(\d+) failed', content)
        if failed_match:
            broken_urls = int(failed_match.group(1))
        
    except Exception as e:
        log_warning(f"Failed to parse non-JSON output: {e}")
    
    success_rate = 0
    if total_urls > 0:
        success_rate = (total_urls - broken_urls) * 100 // total_urls
    
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"total-urls={total_urls}\n")
            f.write(f"broken-urls={broken_urls}\n")
            f.write(f"success-rate={success_rate}%\n")


def validate_urls():
    """Main validation function."""
    log_info("Starting URL validation...")
    
    # Check if urlsup is available
    try:
        subprocess.run(['urlsup', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_error("urlsup binary not found in PATH")
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write("total-urls=0\n")
                f.write("broken-urls=0\n")
                f.write("success-rate=0%\n")
                f.write("exit-code=127\n")
                f.write("report-path=\n")
        sys.exit(127)
    
    # Build command arguments
    cmd_args = build_command()
    
    # Create report file
    github_workspace = os.environ.get('GITHUB_WORKSPACE', '.')
    report_file = Path(github_workspace) / 'urlsup-report.json'
    
    # Log the command that will be executed (for debugging)
    log_info(f"Executing: urlsup {' '.join(cmd_args)}")
    
    # Execute urlsup and capture exit code
    exit_code = 0
    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_stdout, \
             tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_stderr:
            
            result = subprocess.run(
                ['urlsup'] + cmd_args,
                stdout=temp_stdout,
                stderr=temp_stderr,
                text=True
            )
            exit_code = result.returncode
            
            if exit_code != 0:
                log_warning(f"urlsup exited with code {exit_code}")
            
            # Show stderr if there were issues
            temp_stderr.seek(0)
            stderr_content = temp_stderr.read()
            if stderr_content.strip():
                log_info("urlsup stderr output:")
                print(stderr_content, file=sys.stderr)
            
            # Copy stdout to report file
            temp_stdout.seek(0)
            with open(report_file, 'w') as f:
                f.write(temp_stdout.read())
    
    except Exception as e:
        log_error(f"Failed to execute urlsup: {e}")
        exit_code = 1
    finally:
        # Clean up temp files
        try:
            os.unlink(temp_stdout.name)
            os.unlink(temp_stderr.name)
        except:
            pass
    
    # Debug: show first few lines of the output
    log_info("Report file preview:")
    try:
        with open(report_file) as f:
            lines = f.readlines()[:5]
            for line in lines:
                print(line.rstrip(), file=sys.stderr)
    except Exception:
        pass
    
    # Parse results
    parse_results(report_file)
    
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"exit-code={exit_code}\n")
    
    # Determine if we should fail the action
    fail_on_error = to_bool(os.environ.get('INPUT_FAIL_ON_ERROR', 'true'))
    
    # Get the number of broken URLs from the parsed results
    broken_urls_count = 0
    if github_output and Path(github_output).exists():
        try:
            with open(github_output) as f:
                for line in f:
                    if line.startswith('broken-urls='):
                        broken_urls_count = int(line.split('=', 1)[1].strip())
                        break
        except (ValueError, IndexError):
            # Fallback: check JSON directly
            try:
                with open(report_file) as f:
                    data = json.load(f)
                    broken_urls_count = len(data.get('issues', []))
            except:
                broken_urls_count = 0
    
    log_info(f"Detected {broken_urls_count} broken URLs, fail_on_error={fail_on_error}")
    
    # Log the results but never exit with error code during validation
    # The action will handle failing the workflow in a separate step
    if broken_urls_count > 0:
        if fail_on_error:
            log_error(f"URL validation failed with {broken_urls_count} broken URLs")
        else:
            log_warning(f"URL validation found {broken_urls_count} broken URLs, but fail-on-error is disabled")
    else:
        log_success("All URLs are valid!")
    
    # Always exit successfully to ensure annotations and summary are generated
    # The workflow failure will be handled by the action's final step


if __name__ == "__main__":
    validate_urls()