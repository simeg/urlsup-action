#!/usr/bin/env python3
"""
Unit tests for annotate.py script.
"""

import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from annotate import create_annotation, create_annotations, process_non_json_report, process_report


class TestCreateAnnotation(unittest.TestCase):
    """Test annotation creation functionality."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_create_basic_annotation(self, mock_stdout):
        """Test creating basic annotation."""
        result = create_annotation("test.md", 10, "http://broken.com")
        self.assertTrue(result)

        output = mock_stdout.getvalue()
        self.assertIn("::error file=test.md,line=10::", output)
        self.assertIn("http://broken.com", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_create_annotation_with_status(self, mock_stdout):
        """Test creating annotation with status code."""
        result = create_annotation("docs/readme.md", 5, "https://example.com", status="404")
        self.assertTrue(result)

        output = mock_stdout.getvalue()
        self.assertIn("::error file=docs/readme.md,line=5::", output)
        self.assertIn("(HTTP 404)", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_create_annotation_with_error(self, mock_stdout):
        """Test creating annotation with error message."""
        result = create_annotation("test.md", 1, "http://test.com", error="Connection timeout")
        self.assertTrue(result)

        output = mock_stdout.getvalue()
        self.assertIn("Connection timeout", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_create_annotation_full_details(self, mock_stdout):
        """Test creating annotation with all details."""
        result = create_annotation(
            "./docs/guide.md",
            15,
            "https://broken.example.com",
            status="500",
            error="Internal server error",
        )
        self.assertTrue(result)

        output = mock_stdout.getvalue()
        self.assertIn("::error file=docs/guide.md,line=15::", output)
        self.assertIn("(HTTP 500)", output)
        self.assertIn("Internal server error", output)

    def test_create_annotation_invalid_input(self):
        """Test creating annotation with invalid input."""
        result = create_annotation("", 1, "http://test.com")
        self.assertFalse(result)

        result = create_annotation("test.md", "", "http://test.com")
        self.assertFalse(result)

        result = create_annotation("test.md", 1, "")
        self.assertFalse(result)

    @patch("sys.stdout", new_callable=StringIO)
    def test_annotation_path_cleaning(self, mock_stdout):
        """Test that file paths are cleaned correctly."""
        result = create_annotation("./docs/../README.md", 1, "http://test.com")
        self.assertTrue(result)

        output = mock_stdout.getvalue()
        # Should clean up the path
        self.assertNotIn("./", output)
        self.assertNotIn("../", output)


class TestProcessReport(unittest.TestCase):
    """Test report processing functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / "test_report.json"

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_process_nonexistent_file(self):
        """Test processing non-existent file."""
        result = process_report("/nonexistent/file.json")
        self.assertEqual(result, 0)

    @patch("sys.stdout", new_callable=StringIO)
    def test_process_current_format(self, mock_stdout):
        """Test processing current format with issues array."""
        report_data = {
            "status": "failure",
            "issues": [
                {
                    "file": "README.md",
                    "line": 10,
                    "url": "http://broken1.com",
                    "status_code": "404",
                    "description": "Not found",
                },
                {
                    "file": "docs/guide.md",
                    "line": 5,
                    "url": "http://broken2.com",
                    "status_code": "500",
                    "error": "Server error",
                },
            ],
        }

        with open(self.temp_file, "w") as f:
            json.dump(report_data, f)

        result = process_report(str(self.temp_file))
        self.assertEqual(result, 2)

        output = mock_stdout.getvalue()
        self.assertIn("README.md", output)
        self.assertIn("docs/guide.md", output)
        self.assertIn("404", output)
        self.assertIn("500", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_process_older_format_failed_urls(self, mock_stdout):
        """Test processing older format with failed_urls array."""
        report_data = {
            "status": "failure",
            "failed_urls": [
                {
                    "file": "test.md",
                    "line": 3,
                    "url": "http://old-broken.com",
                    "status_code": "404",
                    "error": "Page not found",
                }
            ],
        }

        with open(self.temp_file, "w") as f:
            json.dump(report_data, f)

        result = process_report(str(self.temp_file))
        self.assertEqual(result, 1)

        output = mock_stdout.getvalue()
        self.assertIn("test.md", output)
        self.assertIn("old-broken.com", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_process_alternative_format_results(self, mock_stdout):
        """Test processing alternative format with results array."""
        report_data = {
            "status": "failure",
            "results": [
                {
                    "url": "http://test.com",
                    "success": False,
                    "location": {"file": "docs.md", "line": 7},
                    "result": {"status_code": "403", "error": "Forbidden"},
                },
                {"url": "http://good.com", "success": True},
            ],
        }

        with open(self.temp_file, "w") as f:
            json.dump(report_data, f)

        result = process_report(str(self.temp_file))
        self.assertEqual(result, 1)

        output = mock_stdout.getvalue()
        self.assertIn("docs.md", output)
        self.assertIn("test.com", output)
        self.assertIn("403", output)

    def test_process_invalid_json(self):
        """Test processing invalid JSON file."""
        with open(self.temp_file, "w") as f:
            f.write("invalid json content")

        with patch("annotate.process_non_json_report") as mock_process_non_json:
            mock_process_non_json.return_value = 5
            result = process_report(str(self.temp_file))
            self.assertEqual(result, 5)
            mock_process_non_json.assert_called_once()

    @patch("sys.stdout", new_callable=StringIO)
    def test_process_empty_issues(self, mock_stdout):
        """Test processing report with no broken URLs."""
        report_data = {"status": "success", "issues": []}

        with open(self.temp_file, "w") as f:
            json.dump(report_data, f)

        result = process_report(str(self.temp_file))
        self.assertEqual(result, 0)


class TestProcessNonJsonReport(unittest.TestCase):
    """Test non-JSON report processing."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / "test_output.txt"

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("sys.stdout", new_callable=StringIO)
    def test_process_text_with_urls(self, mock_stdout):
        """Test processing text output with URLs."""
        content = """
        Error: Failed to validate https://broken1.com
        Warning: Could not reach https://broken2.com
        Info: All other URLs are valid
        """

        with open(self.temp_file, "w") as f:
            f.write(content)

        result = process_non_json_report(str(self.temp_file))
        # Should find at least some URLs (limited to 10)
        self.assertGreaterEqual(result, 0)

    def test_process_empty_file(self):
        """Test processing empty file."""
        with open(self.temp_file, "w") as f:
            f.write("")

        result = process_non_json_report(str(self.temp_file))
        self.assertEqual(result, 0)

    def test_process_file_read_error(self):
        """Test processing file with read error."""
        result = process_non_json_report("/nonexistent/file.txt")
        self.assertEqual(result, 0)


class TestCreateAnnotations(unittest.TestCase):
    """Test main annotation creation function."""

    @patch.dict(os.environ, {"REPORT_PATH": "/fake/report.json"}, clear=True)
    @patch("annotate.process_report")
    def test_create_annotations_success(self, mock_process):
        """Test successful annotation creation."""
        mock_process.return_value = 3

        # Should complete without error
        create_annotations()
        mock_process.assert_called_once_with("/fake/report.json")

    @patch.dict(os.environ, {}, clear=True)
    def test_create_annotations_no_report_path(self):
        """Test annotation creation without REPORT_PATH."""
        # Should handle missing environment variable gracefully
        create_annotations()

    @patch.dict(os.environ, {"REPORT_PATH": "/fake/report.json"}, clear=True)
    @patch("annotate.process_report")
    def test_create_annotations_exception(self, mock_process):
        """Test annotation creation with exception."""
        mock_process.side_effect = Exception("Test error")

        # Should handle exception gracefully
        create_annotations()


if __name__ == "__main__":
    unittest.main()
