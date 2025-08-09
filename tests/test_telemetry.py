#!/usr/bin/env python3
"""Unit tests for telemetry functionality."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path for importing
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir.parent / "scripts"))

from common import Telemetry


class TestTelemetry(unittest.TestCase):
    """Test telemetry functionality."""

    def setUp(self):
        """Reset telemetry state before each test."""
        Telemetry._metrics = {}
        # Clear environment variables
        env_vars_to_clear = ["INPUT_TELEMETRY", "GITHUB_REPOSITORY", "RUNNER_OS"]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

    def test_telemetry_enabled_by_default(self):
        """Test that telemetry is enabled by default."""
        self.assertTrue(Telemetry.is_enabled())

    def test_telemetry_can_be_disabled(self):
        """Test that telemetry can be disabled."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "false"}):
            self.assertFalse(Telemetry.is_enabled())

    def test_telemetry_respects_various_false_values(self):
        """Test that telemetry recognizes various false values."""
        false_values = ["false", "False", "FALSE", "0", "no", "off"]
        for value in false_values:
            with self.subTest(value=value):
                Telemetry._metrics = {}  # Reset state between iterations
                with patch.dict(os.environ, {"INPUT_TELEMETRY": value}):
                    self.assertFalse(Telemetry.is_enabled(), f"Failed for value: {value}")

    def test_telemetry_respects_various_true_values(self):
        """Test that telemetry recognizes various true values."""
        true_values = ["true", "True", "TRUE", "1", "yes", "on"]
        for value in true_values:
            with self.subTest(value=value):
                Telemetry._metrics = {}  # Reset state between iterations
                with patch.dict(os.environ, {"INPUT_TELEMETRY": value}):
                    self.assertTrue(Telemetry.is_enabled(), f"Failed for value: {value}")

    def test_timer_functionality_when_enabled(self):
        """Test timer start/end functionality when telemetry is enabled."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "true"}):
            Telemetry.start_timer("test_operation")
            self.assertIn("test_operation_start", Telemetry._metrics)

            # End timer
            duration = Telemetry.end_timer("test_operation")
            self.assertGreaterEqual(duration, 0)
            self.assertIn("test_operation_duration", Telemetry._metrics)
            self.assertEqual(Telemetry._metrics["test_operation_duration"], duration)

    def test_timer_functionality_when_disabled(self):
        """Test timer functionality when telemetry is disabled."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "false"}):
            Telemetry.start_timer("test_operation")
            self.assertNotIn("test_operation_start", Telemetry._metrics)

            duration = Telemetry.end_timer("test_operation")
            self.assertEqual(duration, 0.0)
            self.assertNotIn("test_operation_duration", Telemetry._metrics)

    def test_record_metric_when_enabled(self):
        """Test metric recording when telemetry is enabled."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "true"}):
            Telemetry.record_metric("test_metric", "test_value")
            self.assertEqual(Telemetry._metrics["test_metric"], "test_value")

    def test_record_metric_when_disabled(self):
        """Test metric recording when telemetry is disabled."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "false"}):
            Telemetry.record_metric("test_metric", "test_value")
            self.assertNotIn("test_metric", Telemetry._metrics)

    def test_get_repository_info_when_enabled(self):
        """Test repository info collection when enabled."""
        with patch.dict(
            os.environ,
            {"INPUT_TELEMETRY": "true", "GITHUB_REPOSITORY": "owner/repo", "RUNNER_OS": "Linux"},
        ):
            info = Telemetry.get_repository_info()
            self.assertEqual(info["repo_type"], "public")
            self.assertEqual(info["runner_os"], "Linux")
            self.assertEqual(info["action_version"], "2.0.0")

    def test_get_repository_info_when_disabled(self):
        """Test repository info collection when disabled."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "false"}):
            info = Telemetry.get_repository_info()
            self.assertEqual(info, {})

    def test_get_repository_info_unknown_repo(self):
        """Test repository info with unknown repository."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "true"}):
            info = Telemetry.get_repository_info()
            self.assertEqual(info["repo_type"], "unknown")

    @patch("builtins.print")
    def test_create_telemetry_annotations_when_enabled(self, mock_print):
        """Test telemetry annotation creation when enabled."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "true"}):
            # Set up some metrics
            Telemetry._metrics = {
                "validation_duration": 5.5,
                "setup_duration": 2.1,
                "cache_hit": True,
                "total_files": 25,
            }

            Telemetry.create_telemetry_annotations()

            # Check that annotations were printed
            self.assertTrue(mock_print.called)
            calls = [str(call) for call in mock_print.call_args_list]

            # Check for specific annotation patterns
            validation_call = any("Validation completed in 5.50s" in call for call in calls)
            setup_call = any("Setup completed in 2.10s" in call for call in calls)
            cache_call = any("Binary cache hit" in call for call in calls)
            size_call = any("Size category: medium" in call for call in calls)

            self.assertTrue(validation_call, "Validation annotation not found")
            self.assertTrue(setup_call, "Setup annotation not found")
            self.assertTrue(cache_call, "Cache annotation not found")
            self.assertTrue(size_call, "Size annotation not found")

    @patch("builtins.print")
    def test_create_telemetry_annotations_when_disabled(self, mock_print):
        """Test telemetry annotation creation when disabled."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "false"}):
            Telemetry._metrics = {"validation_duration": 5.5}
            Telemetry.create_telemetry_annotations()
            mock_print.assert_not_called()

    def test_create_summary_metrics_when_enabled(self):
        """Test summary metrics creation when enabled."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "true"}):
            Telemetry._metrics = {
                "validation_duration": 3.5,
                "setup_duration": 1.2,
                "cache_hit": True,
            }

            summary = Telemetry.create_summary_metrics()

            self.assertIn("## 📊 Performance Metrics", summary)
            self.assertIn("3.50s", summary)
            self.assertIn("1.20s", summary)
            self.assertIn("✅ Hit", summary)
            self.assertIn("Great Performance", summary)

    def test_create_summary_metrics_when_disabled(self):
        """Test summary metrics creation when disabled."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "false"}):
            summary = Telemetry.create_summary_metrics()
            self.assertEqual(summary, "")

    def test_create_summary_metrics_slow_performance(self):
        """Test summary metrics with slow performance."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "true"}):
            Telemetry._metrics = {
                "validation_duration": 15.0,
                "setup_duration": 2.0,
                "cache_hit": False,
            }

            summary = Telemetry.create_summary_metrics()

            self.assertIn("15.00s", summary)
            self.assertIn("❌ Miss", summary)
            self.assertIn("Performance Tip", summary)
            self.assertIn("increasing concurrency", summary)

    def test_repository_size_categorization(self):
        """Test repository size categorization logic."""
        test_cases = [(15, "small"), (50, "medium"), (150, "large")]

        with patch.dict(os.environ, {"INPUT_TELEMETRY": "true"}):
            for file_count, expected_size in test_cases:
                with self.subTest(file_count=file_count, expected_size=expected_size):
                    Telemetry._metrics = {"total_files": file_count}
                    with patch("builtins.print") as mock_print:
                        Telemetry.create_telemetry_annotations()
                        calls = [str(call) for call in mock_print.call_args_list]
                        size_call = any(f"Size category: {expected_size}" in call for call in calls)
                        self.assertTrue(
                            size_call, f"Expected {expected_size} for {file_count} files"
                        )

    def test_timer_with_nonexistent_timer(self):
        """Test ending a timer that was never started."""
        with patch.dict(os.environ, {"INPUT_TELEMETRY": "true"}):
            duration = Telemetry.end_timer("nonexistent_timer")
            self.assertEqual(duration, 0.0)


class TestTelemetryIntegration(unittest.TestCase):
    """Integration tests for telemetry with other components."""

    def setUp(self):
        """Reset state before each test."""
        Telemetry._metrics = {}

    def test_validation_utils_to_bool_integration(self):
        """Test that telemetry correctly uses ValidationUtils.to_bool."""
        # Test various input values
        test_cases = [
            ("true", True),
            ("false", False),
            ("1", True),
            ("0", False),
            ("yes", True),
            ("no", False),
            ("", False),
            (None, False),
        ]

        for input_val, expected in test_cases:
            env_val = str(input_val) if input_val is not None else ""
            with patch.dict(os.environ, {"INPUT_TELEMETRY": env_val}):
                result = Telemetry.is_enabled()
                self.assertEqual(result, expected, f"Failed for input: {input_val}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
