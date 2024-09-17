import pytest
from services.SettingsManager import SettingsManager
from models.Project import Project

def test_load_settings(tmpdir):
    config_path = tmpdir.join("exclusion_settings.json")
    config_path.write('{"excluded_dirs": ["node_modules"], "excluded_files": [".env"]}')
    
    # Create a mock project
    project = Project(
        name="test_project",
        start_directory=str(tmpdir),
        excluded_dirs=["node_modules"],
        excluded_files=[".env"]
    )

    # Initialize the SettingsManager with the mock project
    settings_manager = SettingsManager(project)

    assert settings_manager.get_excluded_dirs() == ["node_modules"]
    assert settings_manager.get_excluded_files() == [".env"]

def test_update_settings(tmpdir):
    config_path = tmpdir.join("exclusion_settings.json")
    config_path.write('{"excluded_dirs": ["node_modules"], "excluded_files": [".env"]}')
    
    # Create a mock project
    project = Project(
        name="test_project",
        start_directory=str(tmpdir),
        excluded_dirs=["node_modules"],
        excluded_files=[".env"]
    )

    # Initialize the SettingsManager with the mock project
    settings_manager = SettingsManager(project)
    
    new_settings = {
        "excluded_dirs": ["dist"],
        "excluded_files": ["secrets.txt"]
    }
    
    settings_manager.update_settings(new_settings)

    assert settings_manager.get_excluded_dirs() == ["dist"]
    assert settings_manager.get_excluded_files() == ["secrets.txt"]
