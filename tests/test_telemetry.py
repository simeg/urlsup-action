#!/usr/bin/env python3
"""
Manual testing script for telemetry functionality.
This script allows you to test telemetry features without running the full action.
"""

import os
import sys
import tempfile
import time
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from common import Telemetry


def test_telemetry_enabled():
    """Test telemetry when enabled."""
    print("🧪 Testing telemetry when ENABLED...")

    # Clear previous metrics
    Telemetry._metrics = {}

    # Set environment to enable telemetry
    os.environ["INPUT_TELEMETRY"] = "true"
    os.environ["GITHUB_REPOSITORY"] = "test/repo"
    os.environ["RUNNER_OS"] = "Linux"

    # Test basic functionality
    assert Telemetry.is_enabled(), "Telemetry should be enabled"

    # Test timer functionality
    Telemetry.start_timer("test_operation")
    time.sleep(0.1)  # Small delay to ensure measurable time
    duration = Telemetry.end_timer("test_operation")
    assert duration > 0, f"Duration should be > 0, got {duration}"

    # Test metric recording
    Telemetry.record_metric("test_metric", "test_value")
    assert "test_metric" in Telemetry._metrics, "Metric should be recorded"

    # Test repository info
    repo_info = Telemetry.get_repository_info()
    assert repo_info["repo_type"] == "public", f"Expected public, got {repo_info['repo_type']}"
    assert repo_info["runner_os"] == "Linux", f"Expected Linux, got {repo_info['runner_os']}"

    print("✅ Telemetry enabled tests passed!")


def test_telemetry_disabled():
    """Test telemetry when disabled."""
    print("🧪 Testing telemetry when DISABLED...")

    # Clear previous metrics
    Telemetry._metrics = {}

    # Set environment to disable telemetry
    os.environ["INPUT_TELEMETRY"] = "false"

    # Test basic functionality
    assert not Telemetry.is_enabled(), "Telemetry should be disabled"

    # Test timer functionality (should do nothing)
    Telemetry.start_timer("test_operation")
    time.sleep(0.1)
    duration = Telemetry.end_timer("test_operation")
    assert duration == 0.0, f"Duration should be 0.0 when disabled, got {duration}"

    # Test metric recording (should do nothing)
    Telemetry.record_metric("test_metric", "test_value")
    assert "test_metric" not in Telemetry._metrics, "Metric should not be recorded when disabled"

    # Test repository info (should return empty dict)
    repo_info = Telemetry.get_repository_info()
    assert repo_info == {}, f"Expected empty dict, got {repo_info}"

    print("✅ Telemetry disabled tests passed!")


def test_telemetry_annotations():
    """Test telemetry annotation generation."""
    print("🧪 Testing telemetry annotations...")

    # Clear previous metrics and enable telemetry
    Telemetry._metrics = {}
    os.environ["INPUT_TELEMETRY"] = "true"

    # Set up test metrics
    Telemetry.record_metric("validation_duration", 3.5)
    Telemetry.record_metric("setup_duration", 1.2)
    Telemetry.record_metric("cache_hit", True)
    Telemetry.record_metric("total_files", 45)  # Medium size

    print("Expected annotations:")
    print("::notice title=Performance::Validation completed in 3.50s")
    print("::notice title=Performance::Setup completed in 1.20s")
    print("::notice title=Performance::Binary cache hit - faster execution")
    print("::notice title=Repository::Size category: medium (45 files)")
    print()
    print("Actual annotations:")

    # Generate annotations (will print to stdout)
    Telemetry.create_telemetry_annotations()

    print("✅ Telemetry annotations test completed!")


def test_telemetry_summary():
    """Test telemetry summary generation."""
    print("🧪 Testing telemetry summary generation...")

    # Clear previous metrics and enable telemetry
    Telemetry._metrics = {}
    os.environ["INPUT_TELEMETRY"] = "true"

    # Test case 1: Fast performance
    print("\n📊 Test Case 1: Fast Performance")
    Telemetry._metrics = {"validation_duration": 2.1, "setup_duration": 0.8, "cache_hit": True}

    summary = Telemetry.create_summary_metrics()
    print(summary)
    assert "Great Performance" in summary, "Should show great performance message"
    assert "✅ Hit" in summary, "Should show cache hit"

    # Test case 2: Slow performance
    print("\n📊 Test Case 2: Slow Performance")
    Telemetry._metrics = {"validation_duration": 15.0, "setup_duration": 3.0, "cache_hit": False}

    summary = Telemetry.create_summary_metrics()
    print(summary)
    assert "Performance Tip" in summary, "Should show performance tip"
    assert "❌ Miss" in summary, "Should show cache miss"

    print("✅ Telemetry summary tests passed!")


def test_telemetry_opt_out_values():
    """Test various opt-out values."""
    print("🧪 Testing telemetry opt-out values...")

    # Test values that should disable telemetry
    false_values = ["false", "False", "FALSE", "0", "no", "off", ""]

    for value in false_values:
        os.environ["INPUT_TELEMETRY"] = value
        assert not Telemetry.is_enabled(), f"Value '{value}' should disable telemetry"

    # Test values that should enable telemetry
    true_values = ["true", "True", "TRUE", "1", "yes", "on"]

    for value in true_values:
        os.environ["INPUT_TELEMETRY"] = value
        assert Telemetry.is_enabled(), f"Value '{value}' should enable telemetry"

    print("✅ Telemetry opt-out tests passed!")


def test_github_environment_simulation():
    """Test telemetry in a simulated GitHub Actions environment."""
    print("🧪 Testing GitHub Actions environment simulation...")

    # Create temporary files to simulate GitHub environment
    with tempfile.TemporaryDirectory() as temp_dir:
        github_output = Path(temp_dir) / "github_output"
        github_summary = Path(temp_dir) / "github_summary"

        # Set up GitHub environment variables
        os.environ.update(
            {
                "INPUT_TELEMETRY": "true",
                "GITHUB_WORKSPACE": temp_dir,
                "GITHUB_OUTPUT": str(github_output),
                "GITHUB_STEP_SUMMARY": str(github_summary),
                "GITHUB_RUN_ID": "12345",
                "GITHUB_REPOSITORY": "test/repo",
                "RUNNER_OS": "Linux",
                "SETUP_DURATION": "2.5",
                "CACHE_HIT": "true",
            }
        )

        # Create some fake outputs
        github_output.write_text("total-urls=50\nbroken-urls=2\n")

        # Clear metrics and set up telemetry
        Telemetry._metrics = {}
        Telemetry.record_metric("validation_duration", 4.2)
        Telemetry.record_metric("setup_duration", 2.5)
        Telemetry.record_metric("cache_hit", True)
        Telemetry.record_metric("total_files", 30)

        print("\n📊 Simulated GitHub Actions Environment:")
        print(f"Workspace: {temp_dir}")
        print(f"Output file: {github_output}")
        print(f"Summary file: {github_summary}")
        print("Run ID: 12345")

        print("\n🏷️ Generated Annotations:")
        Telemetry.create_telemetry_annotations()

        print("\n📋 Generated Summary:")
        summary = Telemetry.create_summary_metrics()
        print(summary)

        # Test writing to GitHub summary file
        if summary:
            with open(github_summary, "w") as f:
                f.write("# Test Summary\n\n")
                f.write(summary)

            print(f"\n📄 Summary written to: {github_summary}")
            print("Content:")
            print(github_summary.read_text())

    print("✅ GitHub environment simulation test passed!")


def main():
    """Run all telemetry tests."""
    print("🚀 Starting Telemetry Test Suite")
    print("=" * 50)

    try:
        test_telemetry_enabled()
        print()

        test_telemetry_disabled()
        print()

        test_telemetry_opt_out_values()
        print()

        test_telemetry_annotations()
        print()

        test_telemetry_summary()
        print()

        test_github_environment_simulation()
        print()

        print("🎉 All telemetry tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

    print("\n💡 To test with the full action:")
    print("1. Create a test workflow in .github/workflows/")
    print("2. Set 'telemetry: true' (or omit for default)")
    print("3. Check job summary and annotations in GitHub UI")
    print("4. Try 'telemetry: false' to verify opt-out works")


if __name__ == "__main__":
    main()
