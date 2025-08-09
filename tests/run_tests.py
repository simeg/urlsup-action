#!/usr/bin/env python3
"""
Test runner for urlsup-action unit tests.
Can be used as a fallback when pytest is not available.
"""

import subprocess
import sys
from pathlib import Path


def run_with_poetry():
    """Run tests using Poetry if available."""
    try:
        # Try to run with Poetry
        result = subprocess.run(
            ["poetry", "run", "pytest", "tests/", "-v", "--tb=short"],
            cwd=Path(__file__).parent.parent,
        )
        return result.returncode
    except FileNotFoundError:
        return None


def run_with_pytest():
    """Run tests using pytest directly if available."""
    try:
        # Try to run with pytest
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            cwd=Path(__file__).parent.parent,
        )
        return result.returncode
    except FileNotFoundError:
        return None


def run_with_unittest():
    """Fallback to unittest if pytest is not available."""
    import unittest

    # Add the test directory to the path
    test_dir = Path(__file__).parent
    sys.path.insert(0, str(test_dir))
    sys.path.insert(0, str(test_dir.parent))

    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = test_dir
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    print("🧪 Running urlsup-action tests...")

    # Try Poetry first, then pytest, then unittest
    exit_code = run_with_poetry()

    if exit_code is None:
        print("⚠️  Poetry not found, trying pytest...")
        exit_code = run_with_pytest()

        if exit_code is None:
            print("⚠️  pytest not found, falling back to unittest")
            exit_code = run_with_unittest()

    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

    sys.exit(exit_code)
