"""
GynTree: This file contains unit tests for the SettingsManager class,
verifying proper loading, updating, and application of project settings.
"""

import pytest
import json
from services.SettingsManager import SettingsManager
from models.Project import Project

@pytest.fixture
def mock_project(tmpdir):
    return Project(
        name="test_project",
        start_directory=str(tmpdir),
        excluded_dirs=["node_modules"],
        excluded_files=[".env"]
    )

@pytest.fixture
def settings_manager(mock_project):
    return SettingsManager(mock_project)

def test_load_settings(settings_manager):
    assert settings_manager.get_excluded_dirs() == ["node_modules"]
    assert settings_manager.get_excluded_files() == [".env"]

def test_update_settings(settings_manager):
    new_settings = {
        "excluded_dirs": ["dist"],
        "excluded_files": ["secrets.txt"]
    }
    
    settings_manager.update_settings(new_settings)

    assert settings_manager.get_excluded_dirs() == ["dist"]
    assert settings_manager.get_excluded_files() == ["secrets.txt"]

def test_is_excluded_dir(settings_manager, mock_project):
    assert settings_manager.is_excluded_dir(f"{mock_project.start_directory}/node_modules")
    assert not settings_manager.is_excluded_dir(f"{mock_project.start_directory}/src")

def test_is_excluded_file(settings_manager, mock_project):
    assert settings_manager.is_excluded_file(f"{mock_project.start_directory}/.env")
    assert not settings_manager.is_excluded_file(f"{mock_project.start_directory}/main.py")

def test_add_excluded_dir(settings_manager):
    settings_manager.add_excluded_dir("build")
    assert "build" in settings_manager.get_excluded_dirs()

def test_add_excluded_file(settings_manager):
    settings_manager.add_excluded_file("config.json")
    assert "config.json" in settings_manager.get_excluded_files()

def test_remove_excluded_dir(settings_manager):
    settings_manager.remove_excluded_dir("node_modules")
    assert "node_modules" not in settings_manager.get_excluded_dirs()

def test_remove_excluded_file(settings_manager):
    settings_manager.remove_excluded_file(".env")
    assert ".env" not in settings_manager.get_excluded_files()

def test_save_and_load_settings(settings_manager, tmpdir):
    new_settings = {
        "excluded_dirs": ["dist", "build"],
        "excluded_files": ["secrets.txt", "config.ini"]
    }
    settings_manager.update_settings(new_settings)
    settings_manager.save_settings()

    # Create a new SettingsManager instance to test loading
    new_settings_manager = SettingsManager(settings_manager.project)
    assert new_settings_manager.get_excluded_dirs() == ["dist", "build"]
    assert new_settings_manager.get_excluded_files() == ["secrets.txt", "config.ini"]

def test_invalid_settings_update(settings_manager):
    with pytest.raises(ValueError):
        settings_manager.update_settings({"invalid_key": "value"})

def test_duplicate_exclusions(settings_manager):
    settings_manager.add_excluded_dir("node_modules")
    assert settings_manager.get_excluded_dirs().count("node_modules") == 1

    settings_manager.add_excluded_file(".env")
    assert settings_manager.get_excluded_files().count(".env") == 1