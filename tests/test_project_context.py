import json
import pytest
from services.ProjectContext import ProjectContext
from models.Project import Project
from services.SettingsManager import SettingsManager
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.auto_exclude.AutoExcludeManager import AutoExcludeManager
from services.RootExclusionManager import RootExclusionManager
from services.ProjectTypeDetector import ProjectTypeDetector

@pytest.fixture
def mock_project(tmpdir):
    return Project(
        name="test_project",
        start_directory=str(tmpdir),
        root_exclusions=[],
        excluded_dirs=[],
        excluded_files=[]
    )

@pytest.fixture
def project_context(mock_project):
    return ProjectContext(mock_project)

def test_initialization(project_context):
    assert project_context.project is not None
    assert isinstance(project_context.settings_manager, SettingsManager)
    assert isinstance(project_context.directory_analyzer, DirectoryAnalyzer)
    assert isinstance(project_context.auto_exclude_manager, AutoExcludeManager)
    assert isinstance(project_context.root_exclusion_manager, RootExclusionManager)
    assert isinstance(project_context.project_type_detector, ProjectTypeDetector)

def test_detect_project_types(project_context, tmpdir):
    tmpdir.join("main.py").write("print('Hello, world!')")
    project_context.detect_project_types()
    assert 'python' in project_context.project_types

def test_initialize_root_exclusions(project_context):
    initial_exclusions = set(project_context.settings_manager.get_root_exclusions())
    project_context.initialize_root_exclusions()
    updated_exclusions = set(project_context.settings_manager.get_root_exclusions())
    assert updated_exclusions >= initial_exclusions

def test_trigger_auto_exclude(project_context):
    result = project_context.trigger_auto_exclude()
    assert isinstance(result, str)
    assert len(result) > 0

def test_get_directory_tree(project_context, tmpdir):
    tmpdir.join("test_file.py").write("# Test content")
    tree = project_context.get_directory_tree()
    assert isinstance(tree, dict)
    assert "test_file.py" in str(tree)

def test_save_settings(project_context):
    project_context.settings_manager.add_excluded_dir("test_dir")
    project_context.save_settings()
    reloaded_context = ProjectContext(project_context.project)
    assert "test_dir" in reloaded_context.settings_manager.get_excluded_dirs()

def test_close(project_context):
    project_context.close()
    assert project_context.settings_manager is None
    assert project_context.directory_analyzer is None
    assert project_context.auto_exclude_manager is None
    assert len(project_context.project_types) == 0
    assert project_context.project_type_detector is None

def test_reinitialize_directory_analyzer(project_context):
    original_analyzer = project_context.directory_analyzer
    project_context.reinitialize_directory_analyzer()
    assert project_context.directory_analyzer is not original_analyzer
    assert isinstance(project_context.directory_analyzer, DirectoryAnalyzer)

def test_stop_analysis(project_context, mocker):
    mock_stop = mocker.patch.object(project_context.directory_analyzer, 'stop')
    project_context.stop_analysis()
    mock_stop.assert_called_once()

def test_project_context_with_existing_settings(mock_project, tmpdir):
    # Set up existing settings
    settings_file = tmpdir.join("config", "projects", f"{mock_project.name}.json")
    settings_file.write(json.dumps({
        "root_exclusions": ["existing_root"],
        "excluded_dirs": ["existing_dir"],
        "excluded_files": ["existing_file"]
    }), ensure=True)
    
    context = ProjectContext(mock_project)
    assert "existing_root" in context.settings_manager.get_root_exclusions()
    assert "existing_dir" in context.settings_manager.get_excluded_dirs()
    assert "existing_file" in context.settings_manager.get_excluded_files()

def test_project_context_error_handling(mock_project, mocker):
    mocker.patch('services.SettingsManager.SettingsManager.__init__', side_effect=Exception("Test error"))
    with pytest.raises(Exception):
        ProjectContext(mock_project)