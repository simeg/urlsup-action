#!/usr/bin/env python3
"""
Test script for parallel processing functionality.
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from common import ParallelProcessor, GitHubActions, ValidationUtils, Logger


def create_test_files(temp_dir: Path, count: int = 25) -> None:
    """Create test markdown files with URLs."""
    for i in range(count):
        file_path = temp_dir / f"test_{i:03d}.md"
        content = f"""# Test File {i}

This is test file number {i}.

Links to test:
- [GitHub](https://github.com)
- [Example](https://example.com)
- [Working URL](https://httpstat.us/200)
- [Test {i}](https://httpstat.us/200?test={i})

More content here...
"""
        file_path.write_text(content)
    
    Logger.info(f"Created {count} test files in {temp_dir}")


def test_parallel_processing_logic():
    """Test parallel processing logic without running urlsup."""
    print("🧪 Testing parallel processing logic...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Set up environment
        os.environ.update({
            "INPUT_PARALLEL_PROCESSING": "true",
            "INPUT_FILES": str(temp_path),
            "INPUT_INCLUDE_EXTENSIONS": "md",
            "INPUT_RECURSIVE": "true",
            "GITHUB_WORKSPACE": str(temp_path)
        })
        
        # Create test files
        create_test_files(temp_path, 25)  # 25 files should trigger parallel processing
        
        # Test should_use_parallel_processing
        should_use = ParallelProcessor.should_use_parallel_processing()
        print(f"Should use parallel processing: {should_use}")
        assert should_use, "Should use parallel processing for 25 files"
        
        # Test file discovery
        discovered_files = ParallelProcessor.discover_files()
        print(f"Discovered {len(discovered_files)} files")
        assert len(discovered_files) == 25, f"Expected 25 files, got {len(discovered_files)}"
        
        # Test batch sizing
        batch_size = ParallelProcessor.get_optimal_batch_size()
        print(f"Optimal batch size: {batch_size}")
        assert batch_size >= 1, "Batch size should be at least 1"
        
        # Test batching
        batches = ParallelProcessor.split_files_into_batches(discovered_files, batch_size)
        print(f"Split into {len(batches)} batches")
        assert len(batches) >= 1, "Should have at least 1 batch"
        
        # Verify all files are in batches
        all_files_in_batches = sum(len(batch) for batch in batches)
        assert all_files_in_batches == 25, f"Expected 25 files in batches, got {all_files_in_batches}"
        
        print("✅ Parallel processing logic tests passed!")


def test_parallel_processing_disabled():
    """Test that parallel processing can be disabled."""
    print("🧪 Testing parallel processing disabled...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Set up environment with parallel processing disabled
        os.environ.update({
            "INPUT_PARALLEL_PROCESSING": "false",
            "INPUT_FILES": str(temp_path),
            "GITHUB_WORKSPACE": str(temp_path)
        })
        
        # Create many test files
        create_test_files(temp_path, 50)  # Even with 50 files
        
        # Should not use parallel processing when disabled
        should_use = ParallelProcessor.should_use_parallel_processing()
        print(f"Should use parallel processing (disabled): {should_use}")
        assert not should_use, "Should not use parallel processing when disabled"
        
        print("✅ Parallel processing disabled test passed!")


def test_small_repository():
    """Test that small repositories don't use parallel processing."""
    print("🧪 Testing small repository...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Set up environment
        os.environ.update({
            "INPUT_PARALLEL_PROCESSING": "true",
            "INPUT_FILES": str(temp_path),
            "GITHUB_WORKSPACE": str(temp_path)
        })
        
        # Create few test files (below threshold)
        create_test_files(temp_path, 5)  # Only 5 files
        
        # Should not use parallel processing for small repos
        should_use = ParallelProcessor.should_use_parallel_processing()
        print(f"Should use parallel processing (small repo): {should_use}")
        assert not should_use, "Should not use parallel processing for small repositories"
        
        print("✅ Small repository test passed!")


def test_batch_optimization():
    """Test batch size optimization."""
    print("🧪 Testing batch optimization...")
    
    # Test different concurrency settings
    test_cases = [
        ("1", 1),
        ("4", 4), 
        ("8", 4),  # Should be capped at 4 (conservative default)
        ("", 4),   # Default when not specified
    ]
    
    for concurrency_input, expected_max in test_cases:
        os.environ["INPUT_CONCURRENCY"] = concurrency_input
        batch_size = ParallelProcessor.get_optimal_batch_size()
        print(f"Concurrency {concurrency_input or 'default'} -> batch size {batch_size}")
        assert 1 <= batch_size <= expected_max, f"Batch size {batch_size} not in range 1-{expected_max}"
    
    print("✅ Batch optimization test passed!")


def test_file_discovery():
    """Test file discovery with different configurations."""
    print("🧪 Testing file discovery...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mixed file types
        (temp_path / "test.md").write_text("# Markdown file")
        (temp_path / "test.txt").write_text("Text file")
        (temp_path / "test.html").write_text("<html>HTML file</html>")
        (temp_path / "test.py").write_text("# Python file")
        
        # Create subdirectory
        sub_dir = temp_path / "subdir"
        sub_dir.mkdir()
        (sub_dir / "sub.md").write_text("# Sub markdown")
        
        os.environ.update({
            "INPUT_FILES": str(temp_path),
            "INPUT_RECURSIVE": "true",
            "GITHUB_WORKSPACE": str(temp_path)
        })
        
        # Test different extension filters
        test_cases = [
            ("md", 2),      # test.md + subdir/sub.md
            ("md,txt", 3),  # test.md + test.txt + subdir/sub.md  
            ("html", 1),    # test.html
            ("py", 1),      # test.py when explicitly included
        ]
        
        for extensions, expected_count in test_cases:
            os.environ["INPUT_INCLUDE_EXTENSIONS"] = extensions
            files = ParallelProcessor.discover_files()
            print(f"Extensions '{extensions}' found {len(files)} files")
            assert len(files) == expected_count, f"Expected {expected_count}, got {len(files)} for extensions '{extensions}'"
    
    print("✅ File discovery test passed!")


def test_report_merging():
    """Test report merging functionality."""
    print("🧪 Testing report merging...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test reports
        report1 = {
            "status": "success",
            "issues": [
                {"file": "test1.md", "line": 1, "url": "http://broken1.com", "status_code": "404"}
            ],
            "urls": {"validated": 10, "unique": 8},
            "files": {"total": 5, "processed": 5}
        }
        
        report2 = {
            "status": "failure", 
            "issues": [
                {"file": "test2.md", "line": 2, "url": "http://broken2.com", "status_code": "500"}
            ],
            "urls": {"validated": 15, "unique": 12},
            "files": {"total": 3, "processed": 3}
        }
        
        report1_path = temp_path / "report1.json"
        report2_path = temp_path / "report2.json"
        
        report1_path.write_text(json.dumps(report1))
        report2_path.write_text(json.dumps(report2))
        
        # Test merging
        merged = ParallelProcessor.merge_reports([str(report1_path), str(report2_path)])
        
        print(f"Merged report: {merged}")
        
        # Verify merged results
        assert merged["status"] == "failure", "Should be failure if any report failed"
        assert len(merged["issues"]) == 2, f"Expected 2 issues, got {len(merged['issues'])}"
        assert merged["urls"]["validated"] == 25, f"Expected 25 validated URLs, got {merged['urls']['validated']}"
        assert merged["files"]["total"] == 8, f"Expected 8 total files, got {merged['files']['total']}"
        
    print("✅ Report merging test passed!")


def main():
    """Run all parallel processing tests."""
    print("🚀 Starting Parallel Processing Test Suite")
    print("=" * 50)
    
    try:
        test_parallel_processing_logic()
        print()
        
        test_parallel_processing_disabled()
        print()
        
        test_small_repository()
        print()
        
        test_batch_optimization()
        print()
        
        test_file_discovery()
        print()
        
        test_report_merging()
        print()
        
        print("🎉 All parallel processing tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n💡 To test with real urlsup:")
    print("1. Run action with 'parallel-processing: true'")
    print("2. Check logs for parallel processing messages")
    print("3. Verify performance improvements in telemetry")


if __name__ == "__main__":
    main()