import pytest
import json
import os
from services.SettingsManager import SettingsManager
from models.Project import Project

pytestmark = pytest.mark.unit

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
        "excluded_files": ["secrets.txt"],
        "theme_preference": "dark"
    }
    settings_manager.update_settings(new_settings)
    assert settings_manager.get_root_exclusions() == ["vendor"]
    assert settings_manager.get_excluded_dirs() == ["build"]
    assert settings_manager.get_excluded_files() == ["secrets.txt"]
    assert settings_manager.get_theme_preference() == "dark"

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
        "excluded_files": ["secrets.txt", ".env"],
        "theme_preference": "dark"
    }
    settings_manager.update_settings(new_settings)
    settings_manager.save_settings()

    new_settings_manager = SettingsManager(settings_manager.project)
    assert new_settings_manager.get_root_exclusions() == ["vendor", "node_modules"]
    assert new_settings_manager.get_excluded_dirs() == ["dist", "build"]
    assert new_settings_manager.get_excluded_files() == ["secrets.txt", ".env"]
    assert new_settings_manager.get_theme_preference() == "dark"

def test_get_theme_preference(settings_manager):
    assert settings_manager.get_theme_preference() in ['light', 'dark']

def test_set_theme_preference(settings_manager):
    settings_manager.set_theme_preference('dark')
    assert settings_manager.get_theme_preference() == 'dark'
    settings_manager.set_theme_preference('light')
    assert settings_manager.get_theme_preference() == 'light'

def test_invalid_theme_preference(settings_manager):
    with pytest.raises(ValueError):
        settings_manager.set_theme_preference('invalid_theme')

def test_theme_preference_persistence(settings_manager, tmpdir):
    settings_manager.set_theme_preference('dark')
    settings_manager.save_settings()

    new_settings_manager = SettingsManager(settings_manager.project)
    assert new_settings_manager.get_theme_preference() == 'dark'

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
    assert not settings_manager.is_excluded_file(os.path.join(mock_project.start_directory, "casesensitive.txt"))

def test_settings_persistence(settings_manager, tmpdir):
    new_settings = {
        "root_exclusions": ["test_root"],
        "excluded_dirs": ["test_dir"],
        "excluded_files": ["test_file"],
        "theme_preference": "dark"
    }
    settings_manager.update_settings(new_settings)
    settings_manager.save_settings()

    reloaded_manager = SettingsManager(settings_manager.project)
    assert reloaded_manager.get_root_exclusions() == ["test_root"]
    assert reloaded_manager.get_excluded_dirs() == ["test_dir"]
    assert reloaded_manager.get_excluded_files() == ["test_file"]
    assert reloaded_manager.get_theme_preference() == "dark"

def test_theme_preference_default(settings_manager):
    settings_manager.update_settings({"theme_preference": None})
    assert settings_manager.get_theme_preference() == 'light'

def test_theme_preference_change_signal(settings_manager, qtbot):
    with qtbot.waitSignal(settings_manager.theme_changed, timeout=1000) as blocker:
        settings_manager.set_theme_preference('dark' if settings_manager.get_theme_preference() == 'light' else 'light')
    assert blocker.signal_triggered

def test_config_file_creation(settings_manager, tmpdir):
    settings_manager.save_settings()
    config_file = os.path.join(SettingsManager.config_dir, f"{settings_manager.project.name}.json")
    assert os.path.exists(config_file)

def test_load_non_existent_settings(mock_project, tmpdir):
    SettingsManager.config_dir = str(tmpdir.mkdir("empty_config"))
    new_settings_manager = SettingsManager(mock_project)
    assert new_settings_manager.get_theme_preference() == 'light'  # Default theme
    assert new_settings_manager.get_root_exclusions() == mock_project.root_exclusions
    assert new_settings_manager.get_excluded_dirs() == mock_project.excluded_dirs
    assert new_settings_manager.get_excluded_files() == mock_project.excluded_files

def test_invalid_settings_update(settings_manager):
    with pytest.raises(KeyError):
        settings_manager.update_settings({"invalid_key": "value"})

def test_add_root_exclusion(settings_manager):
    settings_manager.add_root_exclusion("new_root")
    assert "new_root" in settings_manager.get_root_exclusions()

def test_remove_root_exclusion(settings_manager):
    settings_manager.remove_root_exclusion("node_modules")
    assert "node_modules" not in settings_manager.get_root_exclusions()

def test_theme_preference_type(settings_manager):
    settings_manager.set_theme_preference("dark")
    assert isinstance(settings_manager.get_theme_preference(), str)

def test_exclusion_path_normalization(settings_manager, mock_project):
    settings_manager.add_excluded_dir("path/with//double/slashes")
    normalized_path = os.path.normpath("path/with//double/slashes")
    assert normalized_path in settings_manager.get_excluded_dirs()

def test_empty_exclusions(settings_manager):
    settings_manager.update_settings({
        "root_exclusions": [],
        "excluded_dirs": [],
        "excluded_files": []
    })
    assert settings_manager.get_root_exclusions() == []
    assert settings_manager.get_excluded_dirs() == []
    assert settings_manager.get_excluded_files() == []

def test_duplicate_exclusions(settings_manager):
    settings_manager.add_excluded_dir("test_dir")
    settings_manager.add_excluded_dir("test_dir")
    assert settings_manager.get_excluded_dirs().count("test_dir") == 1

def test_relative_path_handling(settings_manager, mock_project):
    relative_path = os.path.relpath("some/relative/path", mock_project.start_directory)
    settings_manager.add_excluded_dir(relative_path)
    assert relative_path in settings_manager.get_excluded_dirs()

def test_absolute_path_handling(settings_manager, mock_project):
    absolute_path = os.path.abspath("some/absolute/path")
    settings_manager.add_excluded_dir(absolute_path)
    relative_path = os.path.relpath(absolute_path, mock_project.start_directory)
    assert relative_path in settings_manager.get_excluded_dirs()