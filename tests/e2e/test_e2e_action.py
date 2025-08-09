#!/usr/bin/env python3
"""
End-to-end tests for urlsup-action using generated test repositories.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path for importing
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir.parent.parent / "scripts"))
sys.path.insert(0, str(test_dir))

from generate_test_links import generate_test_repository


class TestE2EActionWithTestRepository(unittest.TestCase):
    """End-to-end tests using generated test repositories."""

    def setUp(self):
        """Set up test environment with generated test repository."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_repo = generate_test_repository(self.temp_dir)

        # Set up mock GitHub environment
        self.github_workspace = str(self.temp_dir)
        self.github_output = self.temp_dir / "github_output.txt"
        self.github_step_summary = self.temp_dir / "step_summary.md"

        # Create necessary files
        self.github_output.touch()
        self.github_step_summary.touch()

        # Check that urlsup is available for integration tests
        if not self.is_urlsup_available():
            raise RuntimeError(
                "urlsup binary not found in PATH. Please install urlsup first:\n"
                "  cargo install urlsup\n"
                "Or install Rust and then urlsup:\n"
                "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh\n"
                "  source ~/.cargo/env\n"
                "  cargo install urlsup"
            )

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def check_urlsup_available(self):
        """Check if urlsup is available for testing."""
        try:
            result = subprocess.run(
                ["urlsup", "--version"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    @staticmethod
    def is_urlsup_available():
        """Static method to check if urlsup is available."""
        try:
            subprocess.run(
                ["urlsup", "--version"], capture_output=True, text=True, timeout=10, check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def run_validation_script(self, env_vars):
        """Run the validation script with given environment variables."""
        from validate import validate_urls

        # Preserve critical environment variables
        preserved_vars = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "USER": os.environ.get("USER", ""),
            "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        }

        # Set up environment
        test_env = {
            **preserved_vars,
            "GITHUB_WORKSPACE": self.github_workspace,
            "GITHUB_OUTPUT": str(self.github_output),
            **env_vars,
        }

        with patch.dict(os.environ, test_env, clear=True):
            try:
                validate_urls()
                return True
            except SystemExit as e:
                # Handle expected exits
                return e.code == 0

    def parse_github_output(self):
        """Parse the GitHub output file."""
        output_data = {}
        if self.github_output.exists():
            content = self.github_output.read_text()
            for line in content.strip().split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    output_data[key] = value
        return output_data

    def test_validation_working_urls_only(self):
        """Test validation with only working URLs."""
        working_file = self.test_repo / "dir-one" / "working-urls.md"

        success = self.run_validation_script(
            {
                "INPUT_FILES": str(working_file),
                "INPUT_TIMEOUT": "10",
                "INPUT_FAIL_ON_ERROR": "false",  # Use false to handle occasional network timeouts
            }
        )

        self.assertTrue(success, "Validation should succeed with working URLs")

        output = self.parse_github_output()
        total_urls = int(output.get("total-urls", 0))
        broken_urls = int(output.get("broken-urls", 0))

        # Should find multiple URLs
        self.assertGreater(total_urls, 5)

        # Most URLs should work (allow for occasional network timeouts)
        success_rate = ((total_urls - broken_urls) / total_urls) * 100 if total_urls > 0 else 0
        self.assertGreater(success_rate, 75, f"Expected >75% success rate, got {success_rate}%")

    def test_validation_broken_urls_only(self):
        """Test validation with only broken URLs."""
        broken_file = self.test_repo / "dir-one" / "broken-urls.md"

        success = self.run_validation_script(
            {
                "INPUT_FILES": str(broken_file),
                "INPUT_TIMEOUT": "5",
                "INPUT_FAIL_ON_ERROR": "false",  # Don't fail the test
            }
        )

        # Should complete even with broken URLs when fail_on_error=false
        self.assertTrue(success)

        output = self.parse_github_output()
        self.assertGreater(int(output.get("total-urls", 0)), 0)
        self.assertGreater(int(output.get("broken-urls", 0)), 0)

    def test_validation_mixed_urls(self):
        """Test validation with mixed working and broken URLs."""
        mixed_file = self.test_repo / "dir-one" / "dir-two" / "mixed-urls.md"

        success = self.run_validation_script(
            {
                "INPUT_FILES": str(mixed_file),
                "INPUT_TIMEOUT": "10",
                "INPUT_RETRY": "1",
                "INPUT_FAIL_ON_ERROR": "false",
            }
        )

        self.assertTrue(success)

        output = self.parse_github_output()
        total_urls = int(output.get("total-urls", 0))
        broken_urls = int(output.get("broken-urls", 0))

        self.assertGreater(total_urls, 0)
        self.assertGreater(broken_urls, 0)
        self.assertLess(broken_urls, total_urls)  # Should have some working URLs too

    def test_validation_recursive_directory(self):
        """Test recursive validation of entire test directory."""
        success = self.run_validation_script(
            {
                "INPUT_FILES": str(self.test_repo),
                "INPUT_RECURSIVE": "true",
                "INPUT_INCLUDE_EXTENSIONS": "md,txt,rst,html",
                "INPUT_TIMEOUT": "10",
                "INPUT_FAIL_ON_ERROR": "false",
            }
        )

        self.assertTrue(success)

        output = self.parse_github_output()
        total_urls = int(output.get("total-urls", 0))

        # Should find URLs from multiple files and formats
        self.assertGreater(total_urls, 10)

    def test_validation_with_filters(self):
        """Test validation with allowlist and exclude patterns."""
        config_file = self.test_repo / "config-test.md"

        success = self.run_validation_script(
            {
                "INPUT_FILES": str(config_file),
                "INPUT_ALLOWLIST": "github.com,httpstat.us",
                "INPUT_EXCLUDE_PATTERN": "localhost|127\\.0\\.0\\.1",
                "INPUT_ALLOW_STATUS": "200,201,202,204,301",
                "INPUT_TIMEOUT": "10",
                "INPUT_FAIL_ON_ERROR": "false",
            }
        )

        self.assertTrue(success)

        output = self.parse_github_output()
        # Should have found URLs but some filtered out
        self.assertGreater(int(output.get("total-urls", 0)), 0)

    def test_annotation_script_with_test_data(self):
        """Test annotation script with generated test report."""
        from annotate import process_report

        # Create a test report
        test_report = {
            "status": "failure",
            "issues": [
                {
                    "file": "test.md",
                    "line": 5,
                    "url": "https://broken.example.com",
                    "status_code": "404",
                    "description": "Not found",
                },
                {
                    "file": "docs.md",
                    "line": 10,
                    "url": "https://timeout.example.com",
                    "status_code": "timeout",
                    "error": "Connection timeout",
                },
            ],
        }

        report_file = self.temp_dir / "test_report.json"
        with open(report_file, "w") as f:
            json.dump(test_report, f)

        # Process report and count annotations
        with patch("sys.stdout") as mock_stdout:
            count = process_report(str(report_file))

        self.assertEqual(count, 2)
        # Verify annotations were written to stdout
        mock_stdout.write.assert_called()

    def test_summary_script_with_test_data(self):
        """Test summary script with test data."""
        from summary import generate_summary

        test_env = {
            "TOTAL_URLS": "20",
            "BROKEN_URLS": "5",
            "SUCCESS_RATE": "75%",
            "EXIT_CODE": "1",
            "TOTAL_FILES": "4",
            "PROCESSED_FILES": "4",
            "TOTAL_FOUND_URLS": "25",
            "UNIQUE_URLS": "20",
            "GITHUB_STEP_SUMMARY": str(self.github_step_summary),
            "GITHUB_RUN_ID": "12345",
        }

        with patch.dict(os.environ, test_env, clear=True):
            generate_summary()

        # Verify summary was generated
        self.assertTrue(self.github_step_summary.exists())
        content = self.github_step_summary.read_text()

        self.assertIn("75%", content)
        self.assertIn("20", content)  # Total URLs
        self.assertIn("5", content)  # Broken URLs
        self.assertIn("❌", content)  # Failure emoji
        self.assertIn("4/4", content)  # Files processed


class TestE2EActionOffline(unittest.TestCase):
    """End-to-end tests that don't require urlsup binary."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_repo = generate_test_repository(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_command_building_with_test_scenarios(self):
        """Test command building with various test scenarios."""
        from validate import build_command

        # Test scenario 1: Basic recursive scan
        with patch.dict(
            os.environ,
            {
                "INPUT_FILES": str(self.test_repo),
                "INPUT_RECURSIVE": "true",
                "INPUT_INCLUDE_EXTENSIONS": "md,txt,rst,html",
            },
            clear=True,
        ):
            cmd = build_command()
            self.assertIn(str(self.test_repo), cmd)
            self.assertIn("--recursive", cmd)
            self.assertIn("--include", cmd)
            self.assertIn("md,txt,rst,html", cmd)

        # Test scenario 2: Specific files with filters
        working_file = self.test_repo / "dir-one" / "working-urls.md"
        with patch.dict(
            os.environ,
            {
                "INPUT_FILES": str(working_file),
                "INPUT_ALLOWLIST": "github.com,example.com",
                "INPUT_EXCLUDE_PATTERN": "localhost|127\\.0\\.0\\.1",
                "INPUT_TIMEOUT": "30",
            },
            clear=True,
        ):
            cmd = build_command()
            self.assertIn("--allowlist", cmd)
            self.assertIn("github.com,example.com", cmd)
            self.assertIn("--exclude-pattern", cmd)
            self.assertIn("--timeout", cmd)
            self.assertIn("30", cmd)

    def test_test_repository_structure(self):
        """Verify the generated test repository has expected structure."""
        expected_files = [
            "dir-one/working-urls.md",
            "dir-one/broken-urls.md",
            "dir-one/dir-two/mixed-urls.md",
            "config-test.md",
            "urls.txt",
            "documentation.rst",
            "page.html",
        ]

        for file_path in expected_files:
            full_path = self.test_repo / file_path
            self.assertTrue(full_path.exists(), f"Expected file not found: {file_path}")
            self.assertGreater(full_path.stat().st_size, 0, f"File is empty: {file_path}")

    def test_test_repository_content(self):
        """Verify the test repository contains expected URL patterns."""
        working_file = self.test_repo / "dir-one" / "working-urls.md"
        content = working_file.read_text()

        # Should contain working URLs
        self.assertIn("github.com", content)
        self.assertIn("example.com", content)
        self.assertIn("https://", content)

        broken_file = self.test_repo / "dir-one" / "broken-urls.md"
        content = broken_file.read_text()

        # Should contain broken URLs
        self.assertIn("this-domain-does-not-exist", content)
        self.assertIn("localhost", content)
        self.assertIn("127.0.0.1", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
