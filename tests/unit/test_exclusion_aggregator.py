import gc
import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, Optional, Set

import psutil
import pytest

from services.ExclusionAggregator import ExclusionAggregator

pytestmark = pytest.mark.unit

logger = logging.getLogger(__name__)


class ExclusionTestHelper:
    """Helper class for ExclusionAggregator testing"""

    def __init__(self):
        self.initial_memory = None
        self.test_exclusions = {
            "root_exclusions": {os.path.normpath("/path/to/root_exclude")},
            "excluded_dirs": {
                "/path/to/__pycache__",
                "/path/to/.git",
                "/path/to/venv",
                "/path/to/build",
                "/path/to/custom_dir",
            },
            "excluded_files": {
                "/path/to/file.pyc",
                "/path/to/.gitignore",
                "/path/to/__init__.py",
                "/path/to/custom_file.txt",
            },
        }

    def track_memory(self) -> None:
        """Start memory tracking"""
        gc.collect()
        self.initial_memory = psutil.Process().memory_info().rss

    def check_memory_usage(self, operation: str) -> None:
        """Check memory usage after operation"""
        if self.initial_memory is not None:
            gc.collect()
            current_memory = psutil.Process().memory_info().rss
            memory_diff = current_memory - self.initial_memory
            if memory_diff > 10 * 1024 * 1024:  # 10MB threshold
                logger.warning(
                    f"High memory usage after {operation}: {memory_diff / 1024 / 1024:.2f}MB"
                )


@pytest.fixture
def helper():
    """Create test helper instance"""
    return ExclusionTestHelper()


@pytest.mark.timeout(30)
def test_aggregate_exclusions(helper):
    """Test aggregation of exclusions"""
    helper.track_memory()

    aggregated = ExclusionAggregator.aggregate_exclusions(helper.test_exclusions)

    normalized_root = helper.test_exclusions["root_exclusions"].pop()
    normalized_custom = os.path.normpath("/path/to/custom_dir")

    assert "root_exclusions" in aggregated
    assert "excluded_dirs" in aggregated
    assert "excluded_files" in aggregated
    assert normalized_root in aggregated["root_exclusions"]
    assert "common" in aggregated["excluded_dirs"]
    assert "build" in aggregated["excluded_dirs"]
    assert "__pycache__" in aggregated["excluded_dirs"]["common"]
    assert ".git" in aggregated["excluded_dirs"]["common"]
    assert "venv" in aggregated["excluded_dirs"]["common"]
    assert "build" in aggregated["excluded_dirs"]["build"]
    assert normalized_custom in aggregated["excluded_dirs"]["other"]

    helper.check_memory_usage("aggregation")


@pytest.mark.timeout(30)
def test_format_aggregated_exclusions(helper):
    """Test formatting of aggregated exclusions"""
    helper.track_memory()

    aggregated = {
        "root_exclusions": {os.path.normpath("/path/to/root_exclude")},
        "excluded_dirs": {
            "common": {"__pycache__", ".git", "venv"},
            "build": {"build", "dist"},
            "other": {os.path.normpath("/path/to/custom_dir")},
        },
        "excluded_files": {
            "cache": {os.path.normpath("/path/to")},
            "config": {".gitignore", ".dockerignore"},
            "init": {os.path.normpath("/path/to")},
            "other": {os.path.normpath("/path/to/custom_file.txt")},
        },
    }

    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)
    formatted_lines = formatted.split("\n")

    assert "Root Exclusions:" in formatted_lines
    assert f" - {os.path.normpath('/path/to/root_exclude')}" in formatted_lines
    assert "Directories:" in formatted_lines
    assert " Common: .git, __pycache__, venv" in formatted_lines
    assert " Build: build, dist" in formatted_lines
    assert " Other:" in formatted_lines
    assert f" - {os.path.normpath('/path/to/custom_dir')}" in formatted_lines
    assert "Files:" in formatted_lines
    assert " Cache: 1 items" in formatted_lines
    assert " Config: .dockerignore, .gitignore" in formatted_lines
    assert " Init: 1 items" in formatted_lines
    assert " Other:" in formatted_lines
    assert f" - {os.path.normpath('/path/to/custom_file.txt')}" in formatted_lines

    helper.check_memory_usage("formatting")


@pytest.mark.timeout(30)
def test_empty_exclusions(helper):
    """Test handling of empty exclusions"""
    helper.track_memory()

    exclusions = {
        "root_exclusions": set(),
        "excluded_dirs": set(),
        "excluded_files": set(),
    }

    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)

    assert aggregated == {
        "root_exclusions": set(),
        "excluded_dirs": defaultdict(set),
        "excluded_files": defaultdict(set),
    }
    assert formatted == ""

    helper.check_memory_usage("empty exclusions")


@pytest.mark.timeout(30)
def test_only_common_exclusions(helper):
    """Test handling of common exclusions only"""
    helper.track_memory()

    exclusions = {
        "root_exclusions": set(),
        "excluded_dirs": {"/path/to/__pycache__", "/path/to/.git", "/path/to/venv"},
        "excluded_files": {"/path/to/.gitignore"},
    }

    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)

    assert "common" in aggregated["excluded_dirs"]
    assert "config" in aggregated["excluded_files"]
    assert " Common: .git, __pycache__, venv" in formatted
    assert "Config: .gitignore" in formatted

    helper.check_memory_usage("common exclusions")


@pytest.mark.timeout(30)
def test_duplicate_handling(helper):
    """Test handling of duplicate exclusions"""
    helper.track_memory()

    exclusions = {
        "root_exclusions": {"/path/to/root", "/path/to/root"},
        "excluded_dirs": {"/path/to/dir", "/path/to/dir"},
        "excluded_files": {"/path/to/file", "/path/to/file"},
    }

    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)

    assert len(aggregated["root_exclusions"]) == 1
    assert (
        len(
            [
                item
                for sublist in aggregated["excluded_dirs"].values()
                for item in sublist
            ]
        )
        == 1
    )
    assert (
        len(
            [
                item
                for sublist in aggregated["excluded_files"].values()
                for item in sublist
            ]
        )
        == 1
    )

    helper.check_memory_usage("duplicate handling")


@pytest.mark.timeout(30)
def test_path_normalization(helper):
    """Test path normalization in exclusions"""
    helper.track_memory()

    exclusions = {
        "root_exclusions": {"/path//to/root"},
        "excluded_dirs": {"/path//to/dir"},
        "excluded_files": {"/path//to/file"},
    }

    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)

    assert os.path.normpath("/path/to/root") in aggregated["root_exclusions"]
    assert any(
        os.path.normpath("/path/to/dir") in items
        for items in aggregated["excluded_dirs"].values()
    )
    assert any(
        os.path.normpath("/path/to/file") in items
        for items in aggregated["excluded_files"].values()
    )

    helper.check_memory_usage("path normalization")


@pytest.mark.timeout(30)
def test_category_assignment(helper):
    """Test correct category assignment for exclusions"""
    helper.track_memory()

    exclusions = {
        "root_exclusions": set(),
        "excluded_dirs": {
            "/path/to/node_modules",
            "/path/to/dist",
            "/path/to/custom_folder",
        },
        "excluded_files": {
            "/path/to/package-lock.json",
            "/path/to/.env",
            "/path/to/custom.txt",
        },
    }

    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)

    # Debug print to see what categories are actually present
    print("\nAggregated exclusions:", aggregated)

    assert "node_modules" in aggregated["excluded_dirs"]["common"]
    assert "dist" in aggregated["excluded_dirs"]["build"]
    # Check if 'other' category exists first
    assert (
        "other" in aggregated["excluded_dirs"]
    ), "Missing 'other' category in excluded_dirs"
    assert (
        "other" in aggregated["excluded_files"]
    ), "Missing 'other' category in excluded_files"

    # Compare full paths with platform-appropriate separators
    custom_folder_path = os.path.normpath("/path/to/custom_folder")
    custom_txt_path = os.path.normpath("/path/to/custom.txt")

    assert any(
        os.path.normpath(p) == custom_folder_path
        for p in aggregated["excluded_dirs"]["other"]
    )
    assert ".env" in aggregated["excluded_files"]["config"]
    assert any(
        os.path.normpath(p) == custom_txt_path
        for p in aggregated["excluded_files"]["other"]
    )

    helper.check_memory_usage("category assignment")


@pytest.mark.timeout(30)
def test_mixed_path_separators(helper):
    """Test handling of mixed path separators"""
    helper.track_memory()

    exclusions = {
        "root_exclusions": {"/path\\to/root"},
        "excluded_dirs": {"\\path/to\\dir"},
        "excluded_files": {"path\\to/file"},
    }

    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)

    normalized_path = os.path.normpath("/path/to/root")
    assert normalized_path in aggregated["root_exclusions"]
    assert normalized_path in formatted

    helper.check_memory_usage("mixed separators")


@pytest.mark.timeout(30)
def test_nested_paths(helper):
    """Test handling of nested paths"""
    helper.track_memory()

    # Use raw paths in the input
    root_path = "/path/to/root"
    nested_path = "/path/to/root/nested"
    deeper_path = "/path/to/root/nested/deeper"

    exclusions = {
        "root_exclusions": {root_path},
        "excluded_dirs": {nested_path, deeper_path},
        "excluded_files": {"/path/to/root/file.txt", "/path/to/root/nested/file.txt"},
    }

    aggregated = ExclusionAggregator.aggregate_exclusions(exclusions)

    # Debug print
    print("\nAggregated nested paths:", aggregated)

    # Compare normalized paths
    assert os.path.normpath(root_path) in {
        os.path.normpath(p) for p in aggregated["root_exclusions"]
    }
    assert "other" in aggregated["excluded_dirs"], "Missing 'other' category"
    assert any(
        os.path.normpath(p) == os.path.normpath(nested_path)
        for p in aggregated["excluded_dirs"]["other"]
    )
    assert any(
        os.path.normpath(p) == os.path.normpath(deeper_path)
        for p in aggregated["excluded_dirs"]["other"]
    )

    helper.check_memory_usage("nested paths")


@pytest.mark.timeout(30)
def test_memory_efficiency(helper):
    """Test memory efficiency with large exclusion sets"""
    helper.track_memory()

    large_exclusions = {
        "root_exclusions": {f"/root_{i}" for i in range(1000)},
        "excluded_dirs": {f"/dir_{i}" for i in range(1000)},
        "excluded_files": {f"/file_{i}" for i in range(1000)},
    }

    aggregated = ExclusionAggregator.aggregate_exclusions(large_exclusions)
    formatted = ExclusionAggregator.format_aggregated_exclusions(aggregated)

    assert len(formatted) > 0

    gc.collect()
    current_memory = psutil.Process().memory_info().rss
    memory_diff = current_memory - helper.initial_memory
    assert memory_diff < 50 * 1024 * 1024  # Less than 50MB increase

    helper.check_memory_usage("memory efficiency")


@pytest.mark.timeout(30)
def test_error_handling(helper):
    """Test error handling with invalid inputs"""
    helper.track_memory()

    invalid_exclusions = None

    with pytest.raises(ValueError, match="Exclusions must be a dictionary"):
        ExclusionAggregator.aggregate_exclusions(invalid_exclusions)

    incomplete_exclusions = {"root_exclusions": set()}

    aggregated = ExclusionAggregator.aggregate_exclusions(incomplete_exclusions)
    assert isinstance(aggregated["excluded_dirs"], defaultdict)
    assert isinstance(aggregated["excluded_files"], defaultdict)

    helper.check_memory_usage("error handling")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
