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

from common import Telemetry, ValidationUtils
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
        with patch.dict(os.environ, {"INPUT_TIMEOUT_SECONDS": "10"}, clear=True):
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
        with patch.dict(
            os.environ, {"INPUT_RETRY": "3", "INPUT_RETRY_DELAY_MS": "2000"}, clear=True
        ):
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

    def test_format_options(self):
        """Test format options (always JSON)."""
        # Format is always JSON for proper script parsing
        with patch.dict(os.environ, {}, clear=True):
            cmd = build_command()
            self.assertIn("--format", cmd)
            self.assertIn("json", cmd)

    def test_failure_threshold_options(self):
        """Test failure threshold options."""
        # Test no failure threshold (default)
        with patch.dict(os.environ, {}, clear=True):
            cmd = build_command()
            self.assertNotIn("--failure-threshold", cmd)

        # Test empty failure threshold
        with patch.dict(os.environ, {"INPUT_FAILURE_THRESHOLD": ""}, clear=True):
            cmd = build_command()
            self.assertNotIn("--failure-threshold", cmd)

        # Test valid failure threshold values
        test_thresholds = ["10", "25", "50", "75", "100"]
        for threshold in test_thresholds:
            with self.subTest(threshold=threshold):
                with patch.dict(os.environ, {"INPUT_FAILURE_THRESHOLD": threshold}, clear=True):
                    cmd = build_command()
                    self.assertIn("--failure-threshold", cmd)
                    self.assertIn(threshold, cmd)

    def test_show_performance_options(self):
        """Test show-performance parameter handling."""
        # Test default value (false)
        with patch.dict(os.environ, {}, clear=True):
            show_performance = ValidationUtils.to_bool(
                os.environ.get("INPUT_SHOW_PERFORMANCE", "false")
            )
            self.assertFalse(show_performance)

        # Test explicit false
        with patch.dict(os.environ, {"INPUT_SHOW_PERFORMANCE": "false"}, clear=True):
            show_performance = ValidationUtils.to_bool(
                os.environ.get("INPUT_SHOW_PERFORMANCE", "false")
            )
            self.assertFalse(show_performance)

        # Test explicit true
        with patch.dict(os.environ, {"INPUT_SHOW_PERFORMANCE": "true"}, clear=True):
            show_performance = ValidationUtils.to_bool(
                os.environ.get("INPUT_SHOW_PERFORMANCE", "false")
            )
            self.assertTrue(show_performance)

        # Test case insensitive values
        test_true_values = ["True", "TRUE", "1", "yes", "YES"]
        for value in test_true_values:
            with self.subTest(value=value):
                with patch.dict(os.environ, {"INPUT_SHOW_PERFORMANCE": value}, clear=True):
                    show_performance = ValidationUtils.to_bool(
                        os.environ.get("INPUT_SHOW_PERFORMANCE", "false")
                    )
                    self.assertTrue(show_performance)

        test_false_values = ["False", "FALSE", "0", "no", "NO", "off"]
        for value in test_false_values:
            with self.subTest(value=value):
                with patch.dict(os.environ, {"INPUT_SHOW_PERFORMANCE": value}, clear=True):
                    show_performance = ValidationUtils.to_bool(
                        os.environ.get("INPUT_SHOW_PERFORMANCE", "false")
                    )
                    self.assertFalse(show_performance)


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


class TestValidateUrlsTelemetry(unittest.TestCase):
    """Test telemetry integration in validate_urls function."""

    def setUp(self):
        """Reset telemetry state before each test."""
        Telemetry._metrics = {}

    @patch("subprocess.run")
    @patch("validate.build_command")
    @patch("validate.parse_results")
    @patch("builtins.print")  # Mock telemetry annotations
    def test_telemetry_collection_enabled(self, mock_print, mock_parse, mock_build, mock_run):
        """Test that telemetry is collected when enabled."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Version check
            MagicMock(returncode=0),  # Validation
        ]
        mock_build.return_value = ["--format", "json"]
        mock_parse.return_value = True

        with patch.dict(
            os.environ,
            {
                "GITHUB_WORKSPACE": "/fake/workspace",
                "GITHUB_OUTPUT": "/fake/output",
                "INPUT_TELEMETRY": "true",
                "SETUP_DURATION": "1.5",
                "CACHE_HIT": "true",
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open()):
                with patch("tempfile.NamedTemporaryFile"):
                    with patch("os.unlink"):
                        with patch(
                            "pathlib.Path.rglob", return_value=[Path("file1"), Path("file2")]
                        ):
                            validate_urls()

        # Check that telemetry was recorded
        self.assertIn("action_version", Telemetry._metrics)
        self.assertIn("setup_duration", Telemetry._metrics)
        self.assertIn("cache_hit", Telemetry._metrics)
        self.assertIn("total_files", Telemetry._metrics)

        # Check that annotations were created
        self.assertTrue(mock_print.called)

    @patch("subprocess.run")
    @patch("validate.build_command")
    @patch("validate.parse_results")
    def test_telemetry_collection_disabled(self, mock_parse, mock_build, mock_run):
        """Test that telemetry is not collected when disabled."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Version check
            MagicMock(returncode=0),  # Validation
        ]
        mock_build.return_value = ["--format", "json"]
        mock_parse.return_value = True

        with patch.dict(
            os.environ,
            {
                "GITHUB_WORKSPACE": "/fake/workspace",
                "GITHUB_OUTPUT": "/fake/output",
                "INPUT_TELEMETRY": "false",
                "SETUP_DURATION": "1.5",
                "CACHE_HIT": "true",
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open()):
                with patch("tempfile.NamedTemporaryFile"):
                    with patch("os.unlink"):
                        validate_urls()

        # Check that no telemetry was recorded
        self.assertEqual(len(Telemetry._metrics), 0)

    @patch("subprocess.run")
    @patch("validate.build_command")
    @patch("validate.parse_results")
    def test_telemetry_file_count_collection(self, mock_parse, mock_build, mock_run):
        """Test that file count is correctly collected for telemetry."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Version check
            MagicMock(returncode=0),  # Validation
        ]
        mock_build.return_value = ["--format", "json"]
        mock_parse.return_value = True

        # Mock file system to return specific number of files
        fake_files = [Path(f"file{i}") for i in range(25)]  # 25 files = medium size

        with patch.dict(
            os.environ,
            {
                "GITHUB_WORKSPACE": "/fake/workspace",
                "GITHUB_OUTPUT": "/fake/output",
                "INPUT_TELEMETRY": "true",
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open()):
                with patch("tempfile.NamedTemporaryFile"):
                    with patch("os.unlink"):
                        with patch("pathlib.Path.rglob", return_value=fake_files):
                            with patch("builtins.print"):  # Mock annotations
                                validate_urls()

        # Check that file count was recorded correctly
        self.assertEqual(Telemetry._metrics["total_files"], 25)

    @patch("subprocess.run")
    @patch("validate.build_command")
    @patch("validate.parse_results")
    def test_telemetry_setup_duration_parsing(self, mock_parse, mock_build, mock_run):
        """Test that setup duration is correctly parsed from environment."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Version check
            MagicMock(returncode=0),  # Validation
        ]
        mock_build.return_value = ["--format", "json"]
        mock_parse.return_value = True

        test_cases = [
            ("2.5", 2.5),
            ("invalid", 0.0),
            ("", 0.0),
        ]

        for setup_duration_str, expected_value in test_cases:
            with self.subTest(setup_duration=setup_duration_str):
                Telemetry._metrics = {}  # Reset metrics

                # Need to reset mock for each iteration
                mock_run.side_effect = [
                    MagicMock(returncode=0),  # Version check
                    MagicMock(returncode=0),  # Validation
                ]

                with patch.dict(
                    os.environ,
                    {
                        "GITHUB_WORKSPACE": "/fake/workspace",
                        "GITHUB_OUTPUT": "/fake/output",
                        "INPUT_TELEMETRY": "true",
                        "SETUP_DURATION": setup_duration_str,
                        "CACHE_HIT": "true",
                    },
                    clear=True,
                ):
                    with patch("builtins.open", mock_open()):
                        with patch("tempfile.NamedTemporaryFile"):
                            with patch("os.unlink"):
                                with patch("pathlib.Path.rglob", return_value=[]):
                                    with patch("builtins.print"):  # Mock annotations
                                        validate_urls()

                self.assertEqual(Telemetry._metrics["setup_duration"], expected_value)


class TestValidateUrlsMetricRecording(unittest.TestCase):
    """Test that important metrics are properly recorded during validation."""

    def setUp(self):
        """Reset telemetry state before each test."""
        Telemetry._metrics = {}

    @patch("subprocess.run")
    @patch("validate.build_command")
    @patch("validate.parse_results")
    def test_validation_duration_metric_recorded(self, mock_parse, mock_build, mock_run):
        """Test that validation_duration metric is properly recorded."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Version check
            MagicMock(returncode=0),  # Validation
        ]
        mock_build.return_value = ["--format", "json"]
        mock_parse.return_value = True

        with patch.dict(
            os.environ,
            {
                "GITHUB_WORKSPACE": "/fake/workspace",
                "GITHUB_OUTPUT": "/fake/output",
                "INPUT_TELEMETRY": "true",
                "INPUT_PARALLEL_PROCESSING": "false",  # Force non-parallel path
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open()):
                with patch("tempfile.NamedTemporaryFile"):
                    with patch("os.unlink"):
                        with patch("pathlib.Path.rglob", return_value=[]):
                            with patch("builtins.print"):  # Mock annotations
                                validate_urls()

        # Verify validation_duration metric was recorded
        self.assertIn("validation_duration", Telemetry._metrics)
        self.assertIsInstance(Telemetry._metrics["validation_duration"], float)
        self.assertGreaterEqual(Telemetry._metrics["validation_duration"], 0)

    @patch("subprocess.run")
    @patch("validate.build_command")
    @patch("validate.parse_results")
    def test_urlsup_execution_duration_metric_recorded(self, mock_parse, mock_build, mock_run):
        """Test that urlsup_execution_duration metric is properly recorded."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Version check
            MagicMock(returncode=0),  # Validation
        ]
        mock_build.return_value = ["--format", "json"]
        mock_parse.return_value = True

        with patch.dict(
            os.environ,
            {
                "GITHUB_WORKSPACE": "/fake/workspace",
                "GITHUB_OUTPUT": "/fake/output",
                "INPUT_TELEMETRY": "true",
                "INPUT_PARALLEL_PROCESSING": "false",  # Force non-parallel path
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open()):
                with patch("tempfile.NamedTemporaryFile"):
                    with patch("os.unlink"):
                        with patch("pathlib.Path.rglob", return_value=[]):
                            with patch("builtins.print"):  # Mock annotations
                                validate_urls()

        # Verify urlsup_execution_duration metric was recorded
        self.assertIn("urlsup_execution_duration", Telemetry._metrics)
        self.assertIsInstance(Telemetry._metrics["urlsup_execution_duration"], float)
        self.assertGreaterEqual(Telemetry._metrics["urlsup_execution_duration"], 0)

    @patch("subprocess.run")
    @patch("validate.build_command")
    @patch("validate.parse_results")
    def test_both_duration_metrics_recorded_together(self, mock_parse, mock_build, mock_run):
        """Test that both duration metrics are recorded in the same validation run."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Version check
            MagicMock(returncode=0),  # Validation
        ]
        mock_build.return_value = ["--format", "json"]
        mock_parse.return_value = True

        with patch.dict(
            os.environ,
            {
                "GITHUB_WORKSPACE": "/fake/workspace",
                "GITHUB_OUTPUT": "/fake/output",
                "INPUT_TELEMETRY": "true",
                "INPUT_PARALLEL_PROCESSING": "false",  # Force non-parallel path
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open()):
                with patch("tempfile.NamedTemporaryFile"):
                    with patch("os.unlink"):
                        with patch("pathlib.Path.rglob", return_value=[]):
                            with patch("builtins.print"):  # Mock annotations
                                validate_urls()

        # Verify both metrics were recorded
        self.assertIn("validation_duration", Telemetry._metrics)
        self.assertIn("urlsup_execution_duration", Telemetry._metrics)

        # Verify validation_duration >= urlsup_execution_duration (validation includes execution)
        validation_duration = Telemetry._metrics["validation_duration"]
        execution_duration = Telemetry._metrics["urlsup_execution_duration"]
        self.assertGreaterEqual(validation_duration, execution_duration)

    @patch("subprocess.run")
    @patch("validate.build_command")
    @patch("validate.parse_results")
    def test_duration_metrics_not_recorded_when_telemetry_disabled(
        self, mock_parse, mock_build, mock_run
    ):
        """Test that duration metrics are not recorded when telemetry is disabled."""
        mock_run.side_effect = [
            MagicMock(returncode=0),  # Version check
            MagicMock(returncode=0),  # Validation
        ]
        mock_build.return_value = ["--format", "json"]
        mock_parse.return_value = True

        with patch.dict(
            os.environ,
            {
                "GITHUB_WORKSPACE": "/fake/workspace",
                "GITHUB_OUTPUT": "/fake/output",
                "INPUT_TELEMETRY": "false",  # Telemetry disabled
                "INPUT_PARALLEL_PROCESSING": "false",  # Force non-parallel path
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open()):
                with patch("tempfile.NamedTemporaryFile"):
                    with patch("os.unlink"):
                        with patch("pathlib.Path.rglob", return_value=[]):
                            validate_urls()

        # Verify no telemetry metrics were recorded
        self.assertEqual(len(Telemetry._metrics), 0)

    @patch("subprocess.run")
    @patch("validate.ParallelProcessor.should_use_parallel_processing")
    @patch("validate.validate_urls_parallel")
    def test_validation_duration_metric_recorded_in_parallel_path(
        self, mock_parallel_validate, mock_should_use_parallel, mock_run
    ):
        """Test that validation_duration metric is recorded in parallel processing path."""
        # Setup mocks for parallel processing path
        mock_should_use_parallel.return_value = True
        mock_parallel_validate.return_value = None  # validate_urls_parallel doesn't return anything
        mock_run.return_value = MagicMock(returncode=0)  # urlsup version check

        with patch.dict(
            os.environ,
            {
                "GITHUB_WORKSPACE": "/fake/workspace",
                "GITHUB_OUTPUT": "/fake/output",
                "INPUT_TELEMETRY": "true",
                "INPUT_PARALLEL_PROCESSING": "true",  # Enable parallel processing
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open()):
                with patch("validate.parse_results") as mock_parse:
                    mock_parse.return_value = True
                    with patch("builtins.print"):  # Mock annotations
                        validate_urls()

        # Verify validation_duration metric was recorded in parallel path
        self.assertIn("validation_duration", Telemetry._metrics)
        self.assertIsInstance(Telemetry._metrics["validation_duration"], float)
        self.assertGreaterEqual(Telemetry._metrics["validation_duration"], 0)

        # Verify parallel processing was used
        self.assertIn("processing_mode", Telemetry._metrics)
        self.assertEqual(Telemetry._metrics["processing_mode"], "parallel")

        # Verify the parallel validation function was called
        mock_parallel_validate.assert_called_once()

    @patch("subprocess.run")
    @patch("validate.ParallelProcessor.should_use_parallel_processing")
    @patch("validate.validate_urls_parallel")
    def test_validation_duration_metric_not_recorded_in_parallel_path_when_telemetry_disabled(
        self, mock_parallel_validate, mock_should_use_parallel, mock_run
    ):
        """Test that validation_duration metric is not recorded in parallel
        path when telemetry is disabled."""
        # Setup mocks for parallel processing path
        mock_should_use_parallel.return_value = True
        mock_parallel_validate.return_value = None
        mock_run.return_value = MagicMock(returncode=0)  # urlsup version check

        with patch.dict(
            os.environ,
            {
                "GITHUB_WORKSPACE": "/fake/workspace",
                "GITHUB_OUTPUT": "/fake/output",
                "INPUT_TELEMETRY": "false",  # Telemetry disabled
                "INPUT_PARALLEL_PROCESSING": "true",
            },
            clear=True,
        ):
            with patch("builtins.open", mock_open()):
                with patch("validate.parse_results") as mock_parse:
                    mock_parse.return_value = True
                    validate_urls()

        # Verify no telemetry metrics were recorded (telemetry disabled)
        self.assertEqual(len(Telemetry._metrics), 0)

        # Verify the parallel validation function was still called
        mock_parallel_validate.assert_called_once()


class TestSummaryFeatures(unittest.TestCase):
    """Test job summary features for failure threshold and performance metrics."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.summary_file = Path(self.temp_dir) / "summary.md"

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_failure_threshold_display_in_summary(self):
        """Test that failure threshold information is displayed in job summaries."""
        # Mock environment for summary generation
        test_env = {
            "TOTAL_URLS": "100",
            "BROKEN_URLS": "5",
            "SUCCESS_RATE": "95%",
            "INPUT_FAILURE_THRESHOLD": "10",
            "INPUT_SHOW_PERFORMANCE": "false",
            "GITHUB_STEP_SUMMARY": str(self.summary_file),
        }

        with patch.dict(os.environ, test_env, clear=True):
            # Import and run summary generation
            from summary import generate_summary

            generate_summary()

        # Check that summary file was created and contains threshold info
        self.assertTrue(self.summary_file.exists())
        with open(self.summary_file) as f:
            content = f.read()

        # Verify failure threshold information is present
        self.assertIn("Failure Threshold", content)
        self.assertIn("10.0%", content)  # Note: format shows decimal
        self.assertIn("PASSED", content)  # 5% actual < 10% threshold
        self.assertIn("5.0%", content)  # Actual failure rate

    def test_failure_threshold_exceeded_in_summary(self):
        """Test failure threshold exceeded scenario in job summary."""
        test_env = {
            "TOTAL_URLS": "100",
            "BROKEN_URLS": "15",
            "SUCCESS_RATE": "85%",
            "INPUT_FAILURE_THRESHOLD": "10",
            "INPUT_SHOW_PERFORMANCE": "false",
            "GITHUB_STEP_SUMMARY": str(self.summary_file),
        }

        with patch.dict(os.environ, test_env, clear=True):
            from summary import generate_summary

            generate_summary()

        with open(self.summary_file) as f:
            content = f.read()

        # Verify threshold exceeded information
        self.assertIn("Failure Threshold", content)
        self.assertIn("10.0%", content)  # Note: format shows decimal
        self.assertIn("EXCEEDED", content)  # 15% actual > 10% threshold
        self.assertIn("15.0%", content)  # Actual failure rate

    def test_performance_metrics_shown_when_enabled(self):
        """Test that performance metrics are shown when show-performance is true."""
        # Mock telemetry data
        Telemetry._metrics = {
            "setup_duration": 2.5,
            "validation_duration": 10.3,
            "cache_hit": True,
            "total_urls_validated": 50,
        }

        test_env = {
            "TOTAL_URLS": "50",
            "BROKEN_URLS": "0",
            "SUCCESS_RATE": "100%",
            "INPUT_SHOW_PERFORMANCE": "true",
            "GITHUB_STEP_SUMMARY": str(self.summary_file),
        }

        with patch.dict(os.environ, test_env, clear=True):
            from summary import generate_summary

            generate_summary()

        with open(self.summary_file) as f:
            content = f.read()

        # Verify performance metrics are present
        self.assertIn("Performance Metrics", content)
        self.assertIn("2.5", content)  # Setup duration
        self.assertIn("10.3", content)  # Validation duration

    def test_performance_metrics_hidden_when_disabled(self):
        """Test that performance metrics are hidden when show-performance is false."""
        # Mock telemetry data
        Telemetry._metrics = {"setup_duration": 2.5, "validation_duration": 10.3, "cache_hit": True}

        test_env = {
            "TOTAL_URLS": "50",
            "BROKEN_URLS": "0",
            "SUCCESS_RATE": "100%",
            "INPUT_SHOW_PERFORMANCE": "false",
            "GITHUB_STEP_SUMMARY": str(self.summary_file),
        }

        with patch.dict(os.environ, test_env, clear=True):
            from summary import generate_summary

            generate_summary()

        with open(self.summary_file) as f:
            content = f.read()

        # Verify performance metrics are NOT present
        self.assertNotIn("Performance Metrics", content)

    def test_failure_threshold_with_zero_urls(self):
        """Test failure threshold handling when no URLs are found."""
        test_env = {
            "TOTAL_URLS": "0",
            "BROKEN_URLS": "0",
            "SUCCESS_RATE": "0%",
            "INPUT_FAILURE_THRESHOLD": "10",
            "GITHUB_STEP_SUMMARY": str(self.summary_file),
        }

        with patch.dict(os.environ, test_env, clear=True):
            from summary import generate_summary

            generate_summary()

        with open(self.summary_file) as f:
            content = f.read()

        # Should not crash and should show threshold info
        self.assertIn("Failure Threshold", content)
        self.assertIn("PASSED", content)  # 0% failure rate should pass any threshold

    def test_invalid_failure_threshold_handling(self):
        """Test handling of invalid failure threshold values."""
        test_env = {
            "TOTAL_URLS": "100",
            "BROKEN_URLS": "5",
            "SUCCESS_RATE": "95%",
            "INPUT_FAILURE_THRESHOLD": "invalid",
            "GITHUB_STEP_SUMMARY": str(self.summary_file),
        }

        with patch.dict(os.environ, test_env, clear=True):
            from summary import generate_summary

            # Should not crash with invalid threshold
            generate_summary()

        with open(self.summary_file) as f:
            content = f.read()

        # Should not include threshold information for invalid values
        self.assertNotIn("Failure Threshold", content)


class TestFormatParameterIntegration(unittest.TestCase):
    """Test format parameter integration across the validation pipeline."""

    def setUp(self):
        """Reset telemetry state before each test."""
        Telemetry._metrics = {}

    def test_format_parameter_passed_to_urlsup(self):
        """Test that format parameter is always JSON."""
        # Format is always JSON for proper script parsing
        with patch.dict(os.environ, {}, clear=True):
            cmd = build_command()

            # Verify format is always JSON
            self.assertIn("--format", cmd)
            format_index = cmd.index("--format")
            self.assertEqual(cmd[format_index + 1], "json")

    def test_default_format_is_json(self):
        """Test that format is always JSON."""
        with patch.dict(os.environ, {}, clear=True):
            cmd = build_command()
            self.assertIn("--format", cmd)
            format_index = cmd.index("--format")
            self.assertEqual(cmd[format_index + 1], "json")


if __name__ == "__main__":
    unittest.main()
