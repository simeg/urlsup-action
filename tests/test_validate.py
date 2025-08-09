#!/usr/bin/env python3
"""
Unit tests for validate.py script.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Add scripts directory to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from common import ValidationUtils
from validate import build_command, parse_non_json, parse_results, validate_urls


class TestToBool(unittest.TestCase):
    """Test boolean conversion function."""

    def test_true_values(self):
        """Test values that should be True."""
        for value in ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]:
            with self.subTest(value=value):
                self.assertTrue(ValidationUtils.to_bool(value))

    def test_false_values(self):
        """Test values that should be False."""
        for value in ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF", "", None]:
            with self.subTest(value=value):
                self.assertFalse(ValidationUtils.to_bool(value))


class TestBuildCommand(unittest.TestCase):
    """Test command building functionality."""

    def test_default_command(self):
        """Test command with default values."""
        with patch.dict(os.environ, {}, clear=True):
            cmd = build_command()
            self.assertIn(".", cmd)
            self.assertIn("--recursive", cmd)
            self.assertIn("--format", cmd)
            self.assertIn("json", cmd)
            self.assertIn("--no-progress", cmd)

    def test_files_input(self):
        """Test files input processing."""
        with patch.dict(os.environ, {"INPUT_FILES": "README.md CHANGELOG.md"}, clear=True):
            cmd = build_command()
            self.assertIn("README.md", cmd)
            self.assertIn("CHANGELOG.md", cmd)
            self.assertNotIn(".", cmd)

    def test_include_extensions(self):
        """Test include extensions."""
        with patch.dict(os.environ, {"INPUT_INCLUDE_EXTENSIONS": "md,txt,html"}, clear=True):
            cmd = build_command()
            self.assertIn("--include", cmd)
            self.assertIn("md,txt,html", cmd)

    def test_timeout_setting(self):
        """Test timeout setting."""
        with patch.dict(os.environ, {"INPUT_TIMEOUT": "10"}, clear=True):
            cmd = build_command()
            self.assertIn("--timeout", cmd)
            self.assertIn("10", cmd)

    def test_concurrency_setting(self):
        """Test concurrency setting."""
        with patch.dict(os.environ, {"INPUT_CONCURRENCY": "20"}, clear=True):
            cmd = build_command()
            self.assertIn("--concurrency", cmd)
            self.assertIn("20", cmd)

    def test_retry_settings(self):
        """Test retry settings."""
        with patch.dict(os.environ, {"INPUT_RETRY": "3", "INPUT_RETRY_DELAY": "2000"}, clear=True):
            cmd = build_command()
            self.assertIn("--retry", cmd)
            self.assertIn("3", cmd)
            self.assertIn("--retry-delay", cmd)
            self.assertIn("2000", cmd)

    def test_retry_zero_skipped(self):
        """Test that retry=0 is skipped."""
        with patch.dict(os.environ, {"INPUT_RETRY": "0"}, clear=True):
            cmd = build_command()
            self.assertNotIn("--retry", cmd)

    def test_allowlist_and_status(self):
        """Test allowlist and status settings."""
        with patch.dict(
            os.environ,
            {"INPUT_ALLOWLIST": "github.com,example.com", "INPUT_ALLOW_STATUS": "200,404"},
            clear=True,
        ):
            cmd = build_command()
            self.assertIn("--allowlist", cmd)
            self.assertIn("github.com,example.com", cmd)
            self.assertIn("--allow-status", cmd)
            self.assertIn("200,404", cmd)

    def test_exclude_pattern(self):
        """Test exclude pattern."""
        with patch.dict(os.environ, {"INPUT_EXCLUDE_PATTERN": "localhost|example"}, clear=True):
            cmd = build_command()
            self.assertIn("--exclude-pattern", cmd)
            self.assertIn("localhost|example", cmd)

    def test_boolean_flags(self):
        """Test boolean flags."""
        with patch.dict(
            os.environ,
            {
                "INPUT_ALLOW_TIMEOUT": "true",
                "INPUT_QUIET": "true",
                "INPUT_VERBOSE": "true",
                "INPUT_INSECURE": "true",
            },
            clear=True,
        ):
            cmd = build_command()
            self.assertIn("--allow-timeout", cmd)
            self.assertIn("--quiet", cmd)
            self.assertIn("--verbose", cmd)
            self.assertIn("--insecure", cmd)

    def test_user_agent_and_proxy(self):
        """Test user agent and proxy settings."""
        with patch.dict(
            os.environ,
            {"INPUT_USER_AGENT": "MyBot/1.0", "INPUT_PROXY": "http://proxy.example.com:8080"},
            clear=True,
        ):
            cmd = build_command()
            self.assertIn("--user-agent", cmd)
            self.assertIn("MyBot/1.0", cmd)
            self.assertIn("--proxy", cmd)
            self.assertIn("http://proxy.example.com:8080", cmd)

    def test_config_options(self):
        """Test configuration file options."""
        with patch.dict(
            os.environ,
            {"INPUT_CONFIG": "/path/to/config.json", "INPUT_NO_CONFIG": "true"},
            clear=True,
        ):
            cmd = build_command()
            self.assertIn("--config", cmd)
            self.assertIn("/path/to/config.json", cmd)
            self.assertIn("--no-config", cmd)


class TestParseResults(unittest.TestCase):
    """Test result parsing functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / "test_report.json"

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_rich_format(self):
        """Test parsing rich format JSON."""
        rich_data = {
            "status": "failure",
            "urls": {
                "validated": 10,
                "failed": 2,
                "success_rate": 80,
                "unique": 8,
                "total_found": 12,
            },
            "files": {"total": 5, "processed": 4},
            "issues": [{"url": "http://broken.com", "file": "test.md", "line": 1}],
        }

        with open(self.temp_file, "w") as f:
            json.dump(rich_data, f)

        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(self.temp_file) + ".out"}, clear=True):
            result = parse_results(self.temp_file)
            self.assertTrue(result)

    def test_parse_basic_format(self):
        """Test parsing basic format JSON."""
        basic_data = {"status": "success", "issues": []}

        with open(self.temp_file, "w") as f:
            json.dump(basic_data, f)

        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(self.temp_file) + ".out"}, clear=True):
            result = parse_results(self.temp_file)
            self.assertTrue(result)

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file."""
        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(self.temp_file) + ".out"}, clear=True):
            result = parse_results(Path("/nonexistent/file.json"))
            self.assertFalse(result)

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        with open(self.temp_file, "w") as f:
            f.write("invalid json content")

        with patch("validate.parse_non_json") as mock_parse_non_json:
            result = parse_results(self.temp_file)
            self.assertTrue(result)
            mock_parse_non_json.assert_called_once()


class TestParseNonJson(unittest.TestCase):
    """Test non-JSON parsing functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / "test_output.txt"

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_text_output(self):
        """Test parsing text output with patterns."""
        test_content = """
        Processing files...
        10 URLs found
        3 failed
        Validation complete
        """

        with open(self.temp_file, "w") as f:
            f.write(test_content)

        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(self.temp_file) + ".out"}, clear=True):
            parse_non_json(self.temp_file)
            # Should complete without error


class TestValidateUrls(unittest.TestCase):
    """Test main validation function."""

    @patch("subprocess.run")
    def test_urlsup_not_found(self, mock_run):
        """Test behavior when urlsup is not found."""
        mock_run.side_effect = FileNotFoundError()

        with patch.dict(os.environ, {"GITHUB_OUTPUT": "/fake/output"}, clear=True):
            with patch("builtins.open", mock_open()):
                with self.assertRaises(SystemExit) as cm:
                    validate_urls()
                self.assertEqual(cm.exception.code, 127)

    @patch("subprocess.run")
    @patch("validate.build_command")
    @patch("validate.parse_results")
    def test_successful_validation(self, mock_parse, mock_build, mock_run):
        """Test successful validation flow."""
        # Mock urlsup version check
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Version check
            MagicMock(returncode=0),  # Actual validation
        ]
        mock_build.return_value = ["--format", "json"]
        mock_parse.return_value = True

        with patch.dict(
            os.environ,
            {"GITHUB_WORKSPACE": "/fake/workspace", "GITHUB_OUTPUT": "/fake/output"},
            clear=True,
        ):
            with patch("builtins.open", mock_open()):
                with patch("tempfile.NamedTemporaryFile"):
                    with patch("os.unlink"):
                        # Should complete without raising SystemExit
                        validate_urls()

    @patch("subprocess.run")
    @patch("validate.build_command")
    @patch("validate.parse_results")
    def test_validation_with_broken_urls(self, mock_parse, mock_build, mock_run):
        """Test validation with broken URLs."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Version check
            MagicMock(returncode=1),  # Validation with failures
        ]
        mock_build.return_value = ["--format", "json"]
        mock_parse.return_value = True

        with patch.dict(
            os.environ,
            {
                "GITHUB_WORKSPACE": "/fake/workspace",
                "GITHUB_OUTPUT": "/fake/output",
                "INPUT_FAIL_ON_ERROR": "true",
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open()):
                with patch("tempfile.NamedTemporaryFile"):
                    with patch("os.unlink"):
                        # Should complete (action handles failure in separate step)
                        validate_urls()


if __name__ == "__main__":
    unittest.main()
