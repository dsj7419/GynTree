"""
GynTree: This file contains unit tests for the AutoExcludeManager class,
ensuring proper management of auto-exclusion rules across different project types.
"""

import pytest
from services.auto_exclude.AutoExcludeManager import AutoExcludeManager
from services.SettingsManager import SettingsManager
from models.Project import Project

@pytest.fixture
def mock_project(tmpdir):
    return Project(
        name="test_project",
        start_directory=str(tmpdir),
        excluded_dirs=[],
        excluded_files=[]
    )

@pytest.fixture
def auto_exclude_manager(mock_project):
    return AutoExcludeManager(mock_project.start_directory)

def test_initialization(auto_exclude_manager):
    assert auto_exclude_manager.start_directory
    assert auto_exclude_manager.project_types
    assert auto_exclude_manager.exclusion_services

def test_get_grouped_recommendations(auto_exclude_manager, mock_project):
    settings_manager = SettingsManager(mock_project)
    recommendations = auto_exclude_manager.get_grouped_recommendations(settings_manager.settings)
    
    assert 'directories' in recommendations
    assert 'files' in recommendations

def test_check_for_new_exclusions(auto_exclude_manager, mock_project):
    settings_manager = SettingsManager(mock_project)
    has_new_exclusions = auto_exclude_manager.check_for_new_exclusions(settings_manager.settings)
    
    assert isinstance(has_new_exclusions, bool)

def test_get_formatted_recommendations(auto_exclude_manager):
    formatted_recommendations = auto_exclude_manager.get_formatted_recommendations()
    
    assert isinstance(formatted_recommendations, str)
    assert "Directories:" in formatted_recommendations or "Files:" in formatted_recommendations

def test_python_project_detection(tmpdir):
    tmpdir.join("main.py").write("print('Hello, World!')")
    manager = AutoExcludeManager(str(tmpdir))
    assert 'python' in manager.project_types

def test_web_project_detection(tmpdir):
    tmpdir.join("index.html").write("<html></html>")
    manager = AutoExcludeManager(str(tmpdir))
    assert 'web' in manager.project_types

def test_nextjs_project_detection(tmpdir):
    tmpdir.join("next.config.js").write("module.exports = {}")
    manager = AutoExcludeManager(str(tmpdir))
    assert 'nextjs' in manager.project_types

def test_database_project_detection(tmpdir):
    tmpdir.mkdir("migrations")
    manager = AutoExcludeManager(str(tmpdir))
    assert 'database' in manager.project_types

def test_multiple_project_types(tmpdir):
    tmpdir.join("main.py").write("print('Hello, World!')")
    tmpdir.join("index.html").write("<html></html>")
    tmpdir.mkdir("migrations")
    
    manager = AutoExcludeManager(str(tmpdir))
    assert 'python' in manager.project_types
    assert 'web' in manager.project_types
    assert 'database' in manager.project_types

def test_exclusion_services_creation(auto_exclude_manager):
    assert any(service.__class__.__name__ == 'IDEandGitAutoExclude' for service in auto_exclude_manager.exclusion_services)
    assert any(service.__class__.__name__ == 'PythonAutoExclude' for service in auto_exclude_manager.exclusion_services)

def test_new_exclusions_after_settings_update(auto_exclude_manager, mock_project):
    settings_manager = SettingsManager(mock_project)
    initial_check = auto_exclude_manager.check_for_new_exclusions(settings_manager.settings)
    
    # Update settings to exclude all recommendations
    recommendations = auto_exclude_manager.get_grouped_recommendations(settings_manager.settings)
    settings_manager.update_settings(recommendations)
    
    after_update_check = auto_exclude_manager.check_for_new_exclusions(settings_manager.settings)
    
    assert initial_check != after_update_check
    assert not after_update_check  # No new exclusions after updating settings