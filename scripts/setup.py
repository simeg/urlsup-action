#!/usr/bin/env python3
"""
Setup script for urlsup binary - downloads and caches urlsup for GitHub Actions.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from common import GitHubActions, Logger


def get_version_from_binary(binary_path: Path) -> Optional[str]:
    """Extract version from urlsup binary."""
    try:
        result = subprocess.run(
            [str(binary_path), "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            # Extract version number using regex
            match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
            return match.group(1) if match else "unknown"
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def install_urlsup(version: str, cache_dir: Path) -> bool:
    """Install urlsup using cargo."""
    Logger.info("Installing urlsup via cargo...", to_stderr=True)

    cmd = ["cargo", "install", "urlsup", "--root", str(cache_dir), "--force"]

    if version != "latest":
        clean_version = version.lstrip("v")  # Remove 'v' prefix if present
        Logger.info(f"Installing version {clean_version} from crates.io...", to_stderr=True)
        cmd.extend(["--version", clean_version])
    else:
        Logger.info("Installing latest version from crates.io...", to_stderr=True)

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        Logger.error(f"Failed to install urlsup: {e}", to_stderr=True)
        Logger.error(f"stderr: {e.stderr}", to_stderr=True)
        return False


def setup_urlsup() -> None:
    """Main setup function."""
    Logger.info("Setting up urlsup binary...", to_stderr=True)

    version = os.environ.get("URLSUP_VERSION", "latest")
    cache_dir = Path.home() / ".cache" / "urlsup"
    binary_path = cache_dir / "bin" / "urlsup"

    # Create cache directory
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Check if binary already exists and works
    should_install = True
    if binary_path.exists():
        existing_version = get_version_from_binary(binary_path)
        if existing_version:
            # If version is specified and matches existing, skip installation
            if version != "latest":
                requested_version = version.lstrip("v")  # Remove 'v' prefix if present
                if existing_version == requested_version:
                    Logger.success(f"urlsup {existing_version} already installed and cached", to_stderr=True)
                    should_install = False
                else:
                    Logger.info(
                        f"Existing version {existing_version} != requested "
                        f"version {requested_version}, reinstalling...", to_stderr=True
                    )
            else:
                Logger.success(f"urlsup {existing_version} already installed and cached", to_stderr=True)
                should_install = False

    if should_install:
        if not install_urlsup(version, cache_dir):
            Logger.error("Failed to install urlsup", to_stderr=True)
            sys.exit(1)

        # Verify the binary works
        installed_version = get_version_from_binary(binary_path)
        if not installed_version:
            Logger.error("Installed binary is not functional", to_stderr=True)
            binary_path.unlink(missing_ok=True)
            sys.exit(1)

        Logger.success(f"Successfully installed urlsup {installed_version}", to_stderr=True)

    # Add to PATH for subsequent steps
    GitHubActions.append_to_path(str(cache_dir / "bin"))

    # Set output for use in later steps
    final_version = get_version_from_binary(binary_path) or "unknown"
    GitHubActions.write_outputs({
        "binary-path": binary_path,
        "version": final_version,
    })

    Logger.success("urlsup setup complete!", to_stderr=True)


if __name__ == "__main__":
    setup_urlsup()
