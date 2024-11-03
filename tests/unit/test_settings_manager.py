# tests/unit/test_SettingsManager.py
import gc
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Set

import psutil
import pytest

from models.Project import Project
from services.SettingsManager import SettingsManager

pytestmark = pytest.mark.unit

logger = logging.getLogger(__name__)


class SettingsTestHelper:
    """Helper class for SettingsManager testing"""

    def __init__(self, tmpdir: Path):
        self.tmpdir = tmpdir
        self.initial_memory = None
        self.test_settings = {
            "root_exclusions": ["node_modules", ".git"],
            "excluded_dirs": ["dist", "build"],
            "excluded_files": [".env", "package-lock.json"],
            "theme_preference": "light",
        }

    def create_project(self, name: str = "test_project") -> Project:
        """Create a test project instance"""
        return Project(
            name=name,
            start_directory=str(self.tmpdir),
            root_exclusions=self.test_settings["root_exclusions"],
            excluded_dirs=self.test_settings["excluded_dirs"],
            excluded_files=self.test_settings["excluded_files"],
        )

    def create_settings_file(
        self, project_name: str, settings: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Create a settings file with specified content"""
        if settings is None:
            settings = self.test_settings

        config_dir = self.tmpdir / "config" / "projects"
        config_dir.mkdir(parents=True, exist_ok=True)
        settings_file = config_dir / f"{project_name}.json"

        settings_file.write_text(json.dumps(settings, indent=4))
        return settings_file

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
def helper(tmpdir):
    """Create test helper instance"""
    return SettingsTestHelper(Path(tmpdir))


@pytest.fixture
def mock_project(helper):
    """Create mock project instance"""
    return helper.create_project()


@pytest.fixture
def settings_manager(mock_project, helper):
    """Create SettingsManager instance"""
    SettingsManager.config_dir = str(helper.tmpdir / "config")
    return SettingsManager(mock_project)


@pytest.mark.timeout(30)
def test_initialization(settings_manager, helper):
    """Test SettingsManager initialization"""
    helper.track_memory()

    assert settings_manager.project is not None
    assert settings_manager.config_path.endswith(".json")
    assert isinstance(settings_manager.settings, dict)

    helper.check_memory_usage("initialization")


@pytest.mark.timeout(30)
def test_load_settings_with_existing_file(helper):
    """Test loading settings from existing file"""
    helper.track_memory()

    project = helper.create_project()
    settings_file = helper.create_settings_file(project.name)

    manager = SettingsManager(project)
    assert manager.settings == helper.test_settings

    helper.check_memory_usage("load settings")


@pytest.mark.timeout(30)
def test_load_settings_with_missing_file(helper):
    """Test loading settings with no existing file"""
    helper.track_memory()

    project = helper.create_project("new_project")
    manager = SettingsManager(project)

    assert "root_exclusions" in manager.settings
    assert "excluded_dirs" in manager.settings
    assert "excluded_files" in manager.settings
    assert "theme_preference" in manager.settings

    helper.check_memory_usage("missing file")


@pytest.mark.timeout(30)
def test_get_theme_preference(settings_manager, helper):
    """Test theme preference retrieval"""
    helper.track_memory()

    theme = settings_manager.get_theme_preference()
    assert theme in ["light", "dark"]

    helper.check_memory_usage("theme preference")


@pytest.mark.timeout(30)
def test_set_theme_preference(settings_manager, helper):
    """Test theme preference setting"""
    helper.track_memory()

    original_theme = settings_manager.get_theme_preference()
    new_theme = "dark" if original_theme == "light" else "light"

    settings_manager.set_theme_preference(new_theme)
    assert settings_manager.get_theme_preference() == new_theme

    helper.check_memory_usage("set theme")


@pytest.mark.timeout(30)
def test_get_root_exclusions(settings_manager, helper):
    """Test root exclusions retrieval"""
    helper.track_memory()

    exclusions = settings_manager.get_root_exclusions()
    assert isinstance(exclusions, list)
    assert all(isinstance(excl, str) for excl in exclusions)
    assert "node_modules" in exclusions

    helper.check_memory_usage("root exclusions")


@pytest.mark.timeout(30)
def test_exclusion_handling(settings_manager, helper):
    """Test handling of exclusions"""
    helper.track_memory()

    # Test adding exclusions
    settings_manager.add_excluded_dir("test_dir")
    assert "test_dir" in settings_manager.get_excluded_dirs()

    settings_manager.add_excluded_file("test.txt")
    assert "test.txt" in settings_manager.get_excluded_files()

    # Test removing exclusions
    settings_manager.remove_excluded_dir("test_dir")
    assert "test_dir" not in settings_manager.get_excluded_dirs()

    settings_manager.remove_excluded_file("test.txt")
    assert "test.txt" not in settings_manager.get_excluded_files()

    helper.check_memory_usage("exclusion handling")


@pytest.mark.timeout(30)
def test_path_normalization(settings_manager, helper):
    """Test path normalization in exclusions"""
    helper.track_memory()

    path = "path/with//double/slashes"
    settings_manager.add_excluded_dir(path)

    normalized_path = os.path.normpath(path)
    assert normalized_path in settings_manager.get_excluded_dirs()

    helper.check_memory_usage("path normalization")


@pytest.mark.timeout(30)
def test_update_settings(settings_manager, helper):
    """Test settings update functionality"""
    helper.track_memory()

    new_settings = {
        "root_exclusions": ["new_root"],
        "excluded_dirs": ["new_dir"],
        "excluded_files": ["new_file.txt"],
    }

    settings_manager.update_settings(new_settings)
    assert "new_root" in settings_manager.get_root_exclusions()
    assert "new_dir" in settings_manager.get_excluded_dirs()
    assert "new_file.txt" in settings_manager.get_excluded_files()

    helper.check_memory_usage("update settings")


@pytest.mark.timeout(30)
def test_save_settings(settings_manager, helper):
    """Test settings persistence"""
    helper.track_memory()

    settings_manager.add_excluded_dir("test_save_dir")
    settings_manager.save_settings()

    # Load settings in new manager instance
    new_manager = SettingsManager(settings_manager.project)
    assert "test_save_dir" in new_manager.get_excluded_dirs()

    helper.check_memory_usage("save settings")


@pytest.mark.timeout(30)
def test_is_excluded(settings_manager, helper):
    """Test path exclusion checking"""
    helper.track_memory()

    test_dir = os.path.join(settings_manager.project.start_directory, "test_dir")
    test_file = os.path.join(test_dir, "test.txt")

    settings_manager.add_excluded_dir("test_dir")
    assert settings_manager.is_excluded(test_dir)
    assert settings_manager.is_excluded(test_file)

    helper.check_memory_usage("exclusion check")


@pytest.mark.timeout(30)
def test_relative_path_handling(settings_manager, helper):
    """Test relative path handling"""
    helper.track_memory()

    absolute_path = os.path.join(settings_manager.project.start_directory, "subfolder")
    relative_path = os.path.relpath(
        absolute_path, settings_manager.project.start_directory
    )

    settings_manager.add_excluded_dir(relative_path)
    assert settings_manager.is_excluded(absolute_path)

    helper.check_memory_usage("relative paths")


@pytest.mark.timeout(30)
def test_duplicate_exclusions(settings_manager, helper):
    """Test handling of duplicate exclusions"""
    helper.track_memory()

    settings_manager.add_excluded_dir("test_dir")
    settings_manager.add_excluded_dir("test_dir")

    exclusions = settings_manager.get_excluded_dirs()
    assert exclusions.count("test_dir") == 1

    helper.check_memory_usage("duplicates")


@pytest.mark.timeout(30)
def test_wildcard_patterns(settings_manager, helper):
    """Test wildcard pattern exclusions"""
    helper.track_memory()

    # Add patterns with simple wildcards
    settings_manager.add_excluded_file("**/*.log")
    settings_manager.add_excluded_file("**/*.tmp")
    settings_manager.add_excluded_file("temp/*/cache/*.tmp")

    # Prepare test paths
    test_file1 = os.path.join(
        settings_manager.project.start_directory, "logs", "deep", "test.log"
    )
    test_file2 = os.path.join(
        settings_manager.project.start_directory, "temp", "folder1", "cache", "data.tmp"
    )

    os.makedirs(os.path.dirname(test_file1), exist_ok=True)
    os.makedirs(os.path.dirname(test_file2), exist_ok=True)

    assert settings_manager.is_excluded_file(test_file1)
    assert settings_manager.is_excluded_file(test_file2)

    helper.check_memory_usage("wildcards")


@pytest.mark.timeout(30)
def test_empty_settings(helper):
    """Test handling of empty settings file"""
    helper.track_memory()

    project = helper.create_project("empty_settings")
    helper.create_settings_file(project.name, {})

    manager = SettingsManager(project)
    assert isinstance(manager.get_root_exclusions(), list)
    assert isinstance(manager.get_excluded_dirs(), list)
    assert isinstance(manager.get_excluded_files(), list)

    helper.check_memory_usage("empty settings")


@pytest.mark.timeout(30)
def test_invalid_json_handling(helper):
    """Test handling of corrupted settings file"""
    helper.track_memory()

    project = helper.create_project()
    config_dir = helper.tmpdir / "config" / "projects"
    config_dir.mkdir(parents=True, exist_ok=True)
    settings_file = config_dir / f"{project.name}.json"

    # Write invalid JSON
    settings_file.write_text("{invalid_json: }")

    manager = SettingsManager(project)
    # Should fall back to defaults
    assert isinstance(manager.settings, dict)
    assert "root_exclusions" in manager.settings
    assert "excluded_dirs" in manager.settings

    helper.check_memory_usage("invalid json")


@pytest.mark.timeout(30)
def test_concurrent_settings_access(settings_manager, helper):
    """Test thread safety of settings access"""
    helper.track_memory()
    import threading
    import time

    def modify_settings():
        for i in range(5):
            settings_manager.add_excluded_dir(f"test_dir_{i}")
            time.sleep(0.01)  # Simulate real work
            settings_manager.remove_excluded_dir(f"test_dir_{i}")

    def read_settings():
        for _ in range(10):
            _ = settings_manager.get_excluded_dirs()
            time.sleep(0.005)  # Simulate real work

    threads = []
    for _ in range(3):
        t1 = threading.Thread(target=modify_settings)
        t2 = threading.Thread(target=read_settings)
        threads.extend([t1, t2])
        t1.start()
        t2.start()

    for t in threads:
        t.join()

    # Verify settings are still intact
    assert isinstance(settings_manager.get_excluded_dirs(), list)

    helper.check_memory_usage("concurrent access")


@pytest.mark.timeout(30)
def test_unicode_paths(settings_manager, helper):
    """Test handling of Unicode paths"""
    helper.track_memory()

    # Test with Unicode characters
    unicode_dir = "测试/目录/パス"
    unicode_file = "файл.txt"

    settings_manager.add_excluded_dir(unicode_dir)
    settings_manager.add_excluded_file(unicode_file)

    test_dir = os.path.join(settings_manager.project.start_directory, "测试", "目录", "パス")
    test_file = os.path.join(settings_manager.project.start_directory, "файл.txt")

    assert settings_manager.is_excluded(test_dir)
    assert settings_manager.is_excluded_file(test_file)

    helper.check_memory_usage("unicode paths")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
