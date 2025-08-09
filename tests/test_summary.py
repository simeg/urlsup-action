#!/usr/bin/env python3
"""
Unit tests for summary.py script.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from summary import escape_markdown, generate_summary, main, parse_broken_urls_from_report


class TestParsebrokenUrlsFromReport(unittest.TestCase):
    """Test broken URL parsing from report."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / "test_report.json"

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_current_format_issues(self):
        """Test parsing current format with issues array."""
        report_data = {
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
            ]
        }

        with open(self.temp_file, "w") as f:
            json.dump(report_data, f)

        broken_urls = parse_broken_urls_from_report(str(self.temp_file))
        self.assertEqual(len(broken_urls), 2)

        self.assertEqual(broken_urls[0]["file"], "README.md")
        self.assertEqual(broken_urls[0]["line"], 10)
        self.assertEqual(broken_urls[0]["url"], "http://broken1.com")
        self.assertEqual(broken_urls[0]["status_code"], "404")
        self.assertEqual(broken_urls[0]["error"], "Not found")

        self.assertEqual(broken_urls[1]["file"], "docs/guide.md")
        self.assertEqual(broken_urls[1]["error"], "Server error")

    def test_parse_older_format_failed_urls(self):
        """Test parsing older format with failed_urls array."""
        report_data = {
            "failed_urls": [
                {
                    "file": "test.md",
                    "line": 3,
                    "url": "http://old-broken.com",
                    "status_code": "404",
                    "error": "Page not found",
                }
            ]
        }

        with open(self.temp_file, "w") as f:
            json.dump(report_data, f)

        broken_urls = parse_broken_urls_from_report(str(self.temp_file))
        self.assertEqual(len(broken_urls), 1)
        self.assertEqual(broken_urls[0]["url"], "http://old-broken.com")

    def test_parse_alternative_format_results(self):
        """Test parsing alternative format with results array."""
        report_data = {
            "results": [
                {
                    "url": "http://failed.com",
                    "success": False,
                    "location": {"file": "docs.md", "line": 7},
                    "result": {"status_code": "403", "error": "Forbidden"},
                },
                {"url": "http://good.com", "success": True},
            ]
        }

        with open(self.temp_file, "w") as f:
            json.dump(report_data, f)

        broken_urls = parse_broken_urls_from_report(str(self.temp_file))
        self.assertEqual(len(broken_urls), 1)
        self.assertEqual(broken_urls[0]["url"], "http://failed.com")
        self.assertEqual(broken_urls[0]["file"], "docs.md")
        self.assertEqual(broken_urls[0]["line"], 7)

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file."""
        broken_urls = parse_broken_urls_from_report("/nonexistent/file.json")
        self.assertEqual(len(broken_urls), 0)

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        with open(self.temp_file, "w") as f:
            f.write("invalid json")

        broken_urls = parse_broken_urls_from_report(str(self.temp_file))
        self.assertEqual(len(broken_urls), 0)

    def test_parse_limit_results(self):
        """Test that results are limited to 20 items."""
        issues = []
        for i in range(25):
            issues.append(
                {
                    "file": f"file{i}.md",
                    "line": i + 1,
                    "url": f"http://broken{i}.com",
                    "status_code": "404",
                    "description": "Not found",
                }
            )

        report_data = {"issues": issues}

        with open(self.temp_file, "w") as f:
            json.dump(report_data, f)

        broken_urls = parse_broken_urls_from_report(str(self.temp_file))
        self.assertEqual(len(broken_urls), 20)  # Should be limited


class TestEscapeMarkdown(unittest.TestCase):
    """Test markdown escaping functionality."""

    def test_escape_pipe_characters(self):
        """Test escaping pipe characters."""
        result = escape_markdown("text|with|pipes")
        self.assertEqual(result, "text\\|with\\|pipes")

    def test_escape_newlines(self):
        """Test escaping newlines."""
        result = escape_markdown("text\nwith\nnewlines")
        self.assertEqual(result, "text with newlines")

    def test_escape_carriage_returns(self):
        """Test escaping carriage returns."""
        result = escape_markdown("text\rwith\rreturns")
        self.assertEqual(result, "text with returns")

    def test_escape_combined(self):
        """Test escaping combined characters."""
        result = escape_markdown("text|with\npipes\rand\nlines")
        self.assertEqual(result, "text\\|with pipes and lines")

    def test_escape_none_and_numbers(self):
        """Test escaping None values and numbers."""
        self.assertEqual(escape_markdown(None), "None")
        self.assertEqual(escape_markdown(404), "404")


class TestGenerateSummary(unittest.TestCase):
    """Test summary generation functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.summary_file = Path(self.temp_dir) / "summary.md"

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch.dict(
        os.environ,
        {
            "TOTAL_URLS": "10",
            "BROKEN_URLS": "0",
            "SUCCESS_RATE": "100%",
            "EXIT_CODE": "0",
            "GITHUB_STEP_SUMMARY": "",
        },
        clear=True,
    )
    def test_generate_summary_success(self):
        """Test generating summary for successful validation."""
        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(self.summary_file)}):
            generate_summary()

        self.assertTrue(self.summary_file.exists())
        content = self.summary_file.read_text()

        self.assertIn("✅", content)
        self.assertIn("All URLs are working", content)
        self.assertIn("10", content)
        self.assertIn("100%", content)

    @patch.dict(
        os.environ,
        {
            "TOTAL_URLS": "10",
            "BROKEN_URLS": "2",
            "SUCCESS_RATE": "80%",
            "EXIT_CODE": "1",
            "GITHUB_STEP_SUMMARY": "",
        },
        clear=True,
    )
    def test_generate_summary_with_failures(self):
        """Test generating summary with broken URLs."""
        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(self.summary_file)}):
            generate_summary()

        content = self.summary_file.read_text()

        self.assertIn("❌", content)
        self.assertIn("Some URLs are broken", content)
        self.assertIn("2", content)
        self.assertIn("80%", content)

    @patch.dict(
        os.environ,
        {
            "TOTAL_URLS": "0",
            "BROKEN_URLS": "0",
            "SUCCESS_RATE": "0%",
            "EXIT_CODE": "0",
            "GITHUB_STEP_SUMMARY": "",
        },
        clear=True,
    )
    def test_generate_summary_no_urls(self):
        """Test generating summary when no URLs found."""
        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(self.summary_file)}):
            generate_summary()

        content = self.summary_file.read_text()

        self.assertIn("⚠️", content)
        self.assertIn("No URLs found", content)

    @patch.dict(
        os.environ,
        {
            "TOTAL_URLS": "15",
            "BROKEN_URLS": "3",
            "SUCCESS_RATE": "80%",
            "EXIT_CODE": "1",
            "TOTAL_FILES": "5",
            "PROCESSED_FILES": "4",
            "TOTAL_FOUND_URLS": "20",
            "UNIQUE_URLS": "15",
            "GITHUB_STEP_SUMMARY": "",
        },
        clear=True,
    )
    def test_generate_summary_with_rich_metadata(self):
        """Test generating summary with rich metadata."""
        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(self.summary_file)}):
            generate_summary()

        content = self.summary_file.read_text()

        self.assertIn("4/5", content)  # Processed/total files
        self.assertIn("20", content)  # Total found URLs
        self.assertIn("15", content)  # Unique URLs
        self.assertIn("5", content)  # Duplicate URLs (20-15)

    @patch.dict(
        os.environ,
        {
            "TOTAL_URLS": "10",
            "BROKEN_URLS": "2",
            "SUCCESS_RATE": "80%",
            "EXIT_CODE": "1",
            "REPORT_PATH": "/fake/report.json",
            "GITHUB_STEP_SUMMARY": "",
        },
        clear=True,
    )
    @patch("summary.parse_broken_urls_from_report")
    def test_generate_summary_with_broken_url_details(self, mock_parse):
        """Test generating summary with broken URL details."""
        mock_parse.return_value = [
            {
                "file": "README.md",
                "line": 10,
                "url": "http://broken.com",
                "status_code": "404",
                "error": "Not found",
            }
        ]

        with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(self.summary_file)}):
            generate_summary()

        content = self.summary_file.read_text()

        self.assertIn("Broken URLs Details", content)
        self.assertIn("README.md", content)
        self.assertIn("http://broken.com", content)
        self.assertIn("404", content)

    def test_generate_summary_no_github_env(self):
        """Test generating summary without GITHUB_STEP_SUMMARY."""
        with patch.dict(os.environ, {}, clear=True):
            # Should complete without error
            generate_summary()


class TestMain(unittest.TestCase):
    """Test main function."""

    @patch("summary.generate_summary")
    def test_main_success(self, mock_generate):
        """Test main function success."""
        main()
        mock_generate.assert_called_once()

    @patch("summary.generate_summary")
    def test_main_exception(self, mock_generate):
        """Test main function with exception."""
        mock_generate.side_effect = Exception("Test error")

        # Should handle exception gracefully
        main()


if __name__ == "__main__":
    unittest.main()
