import pytest
import json
import os
from services.SettingsManager import SettingsManager
from models.Project import Project

@pytest.fixture
def mock_project(tmpdir):
    return Project(
        name="test_project",
        start_directory=str(tmpdir),
        root_exclusions=["node_modules"],
        excluded_dirs=["dist"],
        excluded_files=[".env"]
    )

@pytest.fixture
def settings_manager(mock_project, tmpdir):
    SettingsManager.config_dir = str(tmpdir.mkdir("config"))
    return SettingsManager(mock_project)

def test_load_settings(settings_manager):
    expected_exclusions = ["node_modules"]
    actual_exclusions = settings_manager.get_root_exclusions()
    assert actual_exclusions == expected_exclusions

def test_update_settings(settings_manager):
    new_settings = {
        "root_exclusions": ["vendor"],
        "excluded_dirs": ["build"],
        "excluded_files": ["secrets.txt"]
    }
    settings_manager.update_settings(new_settings)
    assert settings_manager.get_root_exclusions() == ["vendor"]
    assert settings_manager.get_excluded_dirs() == ["build"]
    assert settings_manager.get_excluded_files() == ["secrets.txt"]

def test_is_root_excluded(settings_manager, mock_project):
    assert settings_manager.is_root_excluded(os.path.join(mock_project.start_directory, "node_modules"))
    assert not settings_manager.is_root_excluded(os.path.join(mock_project.start_directory, "src"))

def test_add_excluded_dir(settings_manager):
    settings_manager.add_excluded_dir("build")
    assert "build" in settings_manager.get_excluded_dirs()

def test_add_excluded_file(settings_manager):
    settings_manager.add_excluded_file("config.json")
    assert "config.json" in settings_manager.get_excluded_files()

def test_remove_excluded_dir(settings_manager):
    settings_manager.remove_excluded_dir("dist")
    assert "dist" not in settings_manager.get_excluded_dirs()

def test_remove_excluded_file(settings_manager):
    settings_manager.remove_excluded_file(".env")
    assert ".env" not in settings_manager.get_excluded_files()

def test_save_and_load_settings(settings_manager, tmpdir):
    new_settings = {
        "root_exclusions": ["vendor", "node_modules"],
        "excluded_dirs": ["dist", "build"],
        "excluded_files": ["secrets.txt", ".env"]
    }
    settings_manager.update_settings(new_settings)
    settings_manager.save_settings()

    # Create a new SettingsManager instance to test loading
    new_settings_manager = SettingsManager(settings_manager.project)
    assert new_settings_manager.get_root_exclusions() == ["vendor", "node_modules"]
    assert new_settings_manager.get_excluded_dirs() == ["dist", "build"]
    assert new_settings_manager.get_excluded_files() == ["secrets.txt", ".env"]

def test_invalid_settings_update(settings_manager):
    with pytest.raises(ValueError):
        settings_manager.update_settings({"invalid_key": "value"})

def test_get_all_exclusions(settings_manager):
    all_exclusions = settings_manager.get_all_exclusions()
    assert "root_exclusions" in all_exclusions
    assert "excluded_dirs" in all_exclusions
    assert "excluded_files" in all_exclusions

def test_is_excluded(settings_manager, mock_project):
    assert settings_manager.is_excluded(os.path.join(mock_project.start_directory, "node_modules", "some_file"))
    assert settings_manager.is_excluded(os.path.join(mock_project.start_directory, "dist", "bundle.js"))
    assert settings_manager.is_excluded(os.path.join(mock_project.start_directory, ".env"))
    assert not settings_manager.is_excluded(os.path.join(mock_project.start_directory, "src", "main.py"))

def test_wildcard_exclusions(settings_manager, mock_project):
    settings_manager.add_excluded_file("*.log")
    assert settings_manager.is_excluded_file(os.path.join(mock_project.start_directory, "app.log"))
    assert settings_manager.is_excluded_file(os.path.join(mock_project.start_directory, "logs", "error.log"))

def test_nested_exclusions(settings_manager, mock_project):
    settings_manager.add_excluded_dir("nested/dir")
    assert settings_manager.is_excluded_dir(os.path.join(mock_project.start_directory, "nested", "dir"))
    assert settings_manager.is_excluded_dir(os.path.join(mock_project.start_directory, "nested", "dir", "subdir"))

def test_case_sensitivity(settings_manager, mock_project):
    settings_manager.add_excluded_file("CaseSensitive.txt")
    assert settings_manager.is_excluded_file(os.path.join(mock_project.start_directory, "CaseSensitive.txt"))
    assert settings_manager.is_excluded_file(os.path.join(mock_project.start_directory, "casesensitive.txt"))

def test_settings_persistence(settings_manager, tmpdir):
    new_settings = {
        "root_exclusions": ["test_root"],
        "excluded_dirs": ["test_dir"],
        "excluded_files": ["test_file"]
    }
    settings_manager.update_settings(new_settings)
    settings_manager.save_settings()

    # Simulate application restart by creating a new SettingsManager
    reloaded_manager = SettingsManager(settings_manager.project)
    assert reloaded_manager.get_root_exclusions() == ["test_root"]
    assert reloaded_manager.get_excluded_dirs() == ["test_dir"]
    assert reloaded_manager.get_excluded_files() == ["test_file"]