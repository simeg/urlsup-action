#!/usr/bin/env python3
"""Script to fetch the latest urlsup version from crates.io and update action.yml.

This script performs a single, focused task:
1. Fetches the latest version from the crates.io API
2. Updates the urlsup-version default value in action.yml
"""

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Tuple


class VersionUpdater:
    """Handles fetching and updating urlsup version."""

    CRATES_API_URL = "https://crates.io/api/v1/crates/urlsup"
    USER_AGENT = "urlsup-action-version-updater/1.0"
    TIMEOUT_SECONDS = 30
    FILE_TO_UPDATE = "action.yml"

    def __init__(self, repo_root: Path):
        """Initialize with repository root path."""
        self.repo_root = repo_root
        self.action_yml_path = repo_root / self.FILE_TO_UPDATE

    def fetch_latest_version(self) -> str:
        """Fetch the latest version of urlsup from crates.io API.

        Returns
        -------
        str
            The latest version string

        Raises
        ------
        Exception
            If fetching or parsing fails

        """
        print("🌐 Fetching latest version from crates.io...")

        try:
            request = self._create_api_request()
            response_data = self._fetch_api_response(request)
            version = self._extract_version_from_response(response_data)

            print(f"Found version: {version}")
            return version

        except Exception as e:
            raise Exception(f"Failed to fetch version from crates.io: {e}")

    def _create_api_request(self) -> urllib.request.Request:
        """Create the HTTP request for the crates.io API."""
        return urllib.request.Request(
            self.CRATES_API_URL,
            headers={"User-Agent": self.USER_AGENT, "Accept": "application/json"},
        )

    def _fetch_api_response(self, request: urllib.request.Request) -> dict:
        """Fetch and parse the API response.

        Parameters
        ----------
        request : urllib.request.Request
            The prepared HTTP request

        Returns
        -------
        dict
            Parsed JSON response

        Raises
        ------
        Exception
            If network request or JSON parsing fails

        """
        # Security: Validate URL scheme to prevent file:// or other schemes
        if not request.full_url.startswith("https://"):
            raise Exception(f"Only HTTPS URLs are allowed, got: {request.full_url}")

        try:
            with urllib.request.urlopen(
                request, timeout=self.TIMEOUT_SECONDS
            ) as response:  # nosec B310
                content = response.read().decode("utf-8")
            return json.loads(content)
        except urllib.error.URLError as e:
            raise Exception(f"Network error: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}")

    def _extract_version_from_response(self, data: dict) -> str:
        """Extract version from API response.

        Parameters
        ----------
        data : dict
            Parsed JSON response

        Returns
        -------
        str
            Version string

        Raises
        ------
        ValueError
            If version not found in response

        """
        if not isinstance(data, dict):
            raise ValueError("API response is not a valid JSON object")

        crate_info = data.get("crate")
        if not crate_info:
            raise ValueError("No 'crate' field found in API response")

        version = crate_info.get("newest_version")
        if not version:
            raise ValueError("No 'newest_version' field found in crate data")

        return version

    def update_action_yml(self, new_version: str) -> Tuple[str, str]:
        """Update the urlsup-version default value in action.yml.

        Parameters
        ----------
        new_version : str
            The new version to set

        Returns
        -------
        Tuple[str, str]
            (old_version_display, new_version_display)

        Raises
        ------
        Exception
            If file operations or parsing fails

        """
        print(f"📝 Updating {self.action_yml_path}...")

        try:
            lines = self._read_action_yml()
            urlsup_section_idx = self._find_urlsup_version_section(lines)
            default_line_idx = self._find_default_line(lines, urlsup_section_idx)
            old_version = self._update_default_line(lines, default_line_idx, new_version)
            self._write_action_yml(lines)

            return f"default: '{old_version}'", f"default: '{new_version}'"

        except Exception as e:
            raise Exception(f"Failed to update action.yml: {e}")

    def _read_action_yml(self) -> List[str]:
        """Read action.yml file and return lines."""
        try:
            with open(self.action_yml_path, "r") as f:
                return f.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"action.yml not found: {self.action_yml_path}")
        except IOError as e:
            raise IOError(f"Failed to read action.yml: {e}")

    def _find_urlsup_version_section(self, lines: List[str]) -> int:
        """Find the line index of the urlsup-version section.

        Parameters
        ----------
        lines : List[str]
            List of file lines

        Returns
        -------
        int
            Line index of urlsup-version section

        Raises
        ------
        ValueError
            If section not found

        """
        for i, line in enumerate(lines):
            if re.match(r"\s*urlsup-version:\s*$", line):
                return i

        raise ValueError("Could not find 'urlsup-version:' section in action.yml")

    def _find_default_line(self, lines: List[str], start_idx: int) -> int:
        """Find the default line within the urlsup-version section.

        Parameters
        ----------
        lines : List[str]
            List of file lines
        start_idx : int
            Index to start searching from

        Returns
        -------
        int
            Line index of default line

        Raises
        ------
        ValueError
            If default line not found

        """
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]

            # Stop if we've reached another top-level key
            if re.match(r"^[a-zA-Z]", line) and ":" in line:
                break

            # Found the default line
            if re.match(r'\s*default:\s*[\'"]', line):
                return i

        raise ValueError("Could not find 'default:' line in urlsup-version section")

    def _update_default_line(self, lines: List[str], line_idx: int, new_version: str) -> str:
        """Update the default line with new version.

        Parameters
        ----------
        lines : List[str]
            List of file lines
        line_idx : int
            Index of the default line
        new_version : str
            New version to set

        Returns
        -------
        str
            The old version that was replaced

        Raises
        ------
        ValueError
            If line format cannot be parsed

        """
        original_line = lines[line_idx]

        # Parse the line to extract components
        match = re.match(r'(\s*default:\s*)([\'"])(.*?)([\'"])', original_line)
        if not match:
            raise ValueError(f"Could not parse default line format: {original_line.strip()}")

        prefix, quote_char, old_version, quote_char_end = match.groups()

        # Create the new line preserving formatting
        new_line = f"{prefix}{quote_char}{new_version}{quote_char_end}\n"
        lines[line_idx] = new_line

        return old_version

    def _write_action_yml(self, lines: List[str]) -> None:
        """Write the updated lines back to action.yml."""
        try:
            with open(self.action_yml_path, "w") as f:
                f.writelines(lines)
        except IOError as e:
            raise IOError(f"Failed to write action.yml: {e}")


def main():
    """Orchestrate the version update process."""
    try:
        # Initialize with repository root
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent

        # Create updater and perform update
        updater = VersionUpdater(repo_root)
        latest_version = updater.fetch_latest_version()
        old_version_display, new_version_display = updater.update_action_yml(latest_version)

        # Report success
        print("✅ Successfully updated action.yml!")
        print(f"  Old: {old_version_display}")
        print(f"  New: {new_version_display}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
