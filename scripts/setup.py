#!/usr/bin/env python3
"""
Setup script for urlsup binary - downloads and caches urlsup for GitHub Actions.
"""

import os
import sys
import subprocess
import re
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


def get_version_from_binary(binary_path):
    """Extract version from urlsup binary."""
    try:
        result = subprocess.run(
            [str(binary_path), '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # Extract version number using regex
            match = re.search(r'(\d+\.\d+\.\d+)', result.stdout)
            return match.group(1) if match else "unknown"
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def install_urlsup(version, cache_dir):
    """Install urlsup using cargo."""
    log_info("Installing urlsup via cargo...")
    
    cmd = ['cargo', 'install', 'urlsup', '--root', str(cache_dir), '--force']
    
    if version != "latest":
        clean_version = version.lstrip('v')  # Remove 'v' prefix if present
        log_info(f"Installing version {clean_version} from crates.io...")
        cmd.extend(['--version', clean_version])
    else:
        log_info("Installing latest version from crates.io...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to install urlsup: {e}")
        log_error(f"stderr: {e.stderr}")
        return False


def setup_urlsup():
    """Main setup function."""
    log_info("Setting up urlsup binary...")
    
    version = os.environ.get('URLSUP_VERSION', 'latest')
    cache_dir = Path.home() / '.cache' / 'urlsup'
    binary_path = cache_dir / 'bin' / 'urlsup'
    
    # Create cache directory
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if binary already exists and works
    should_install = True
    if binary_path.exists():
        existing_version = get_version_from_binary(binary_path)
        if existing_version:
            # If version is specified and matches existing, skip installation
            if version != "latest":
                requested_version = version.lstrip('v')  # Remove 'v' prefix if present
                if existing_version == requested_version:
                    log_success(f"urlsup {existing_version} already installed and cached")
                    should_install = False
                else:
                    log_info(f"Existing version {existing_version} != requested version {requested_version}, reinstalling...")
            else:
                log_success(f"urlsup {existing_version} already installed and cached")
                should_install = False
    
    if should_install:
        if not install_urlsup(version, cache_dir):
            log_error("Failed to install urlsup")
            sys.exit(1)
        
        # Verify the binary works
        installed_version = get_version_from_binary(binary_path)
        if not installed_version:
            log_error("Installed binary is not functional")
            binary_path.unlink(missing_ok=True)
            sys.exit(1)
        
        log_success(f"Successfully installed urlsup {installed_version}")
    
    # Add to PATH for subsequent steps
    github_path = os.environ.get('GITHUB_PATH')
    if github_path:
        with open(github_path, 'a') as f:
            f.write(f"{cache_dir / 'bin'}\n")
    
    # Set output for use in later steps
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        final_version = get_version_from_binary(binary_path) or 'unknown'
        with open(github_output, 'a') as f:
            f.write(f"binary-path={binary_path}\n")
            f.write(f"version={final_version}\n")
    
    log_success("urlsup setup complete!")


if __name__ == "__main__":
    setup_urlsup()