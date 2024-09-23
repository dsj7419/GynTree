import json
import pytest
from services.ProjectContext import ProjectContext
from models.Project import Project
from services.SettingsManager import SettingsManager
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.auto_exclude.AutoExcludeManager import AutoExcludeManager
from services.RootExclusionManager import RootExclusionManager
from services.ProjectTypeDetector import ProjectTypeDetector
from utilities.theme_manager import ThemeManager

pytestmark = pytest.mark.integration

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
    tmpdir.join("main.py").write("print('Hello, World!')")
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
    settings_file = tmpdir.join("config", "projects", f"{mock_project.name}.json")
    settings_file.write(json.dumps({
        "root_exclusions": ["existing_root"],
        "excluded_dirs": ["existing_dir"],
        "excluded_files": ["existing_file"],
        "theme_preference": "dark"
    }), ensure=True)
    context = ProjectContext(mock_project)
    assert "existing_root" in context.settings_manager.get_root_exclusions()
    assert "existing_dir" in context.settings_manager.get_excluded_dirs()
    assert "existing_file" in context.settings_manager.get_excluded_files()
    assert context.get_theme_preference() == "dark"

def test_project_context_error_handling(mock_project, mocker):
    mocker.patch('services.settings_manager.SettingsManager.__init__', side_effect=Exception("Test error"))
    with pytest.raises(Exception):
        ProjectContext(mock_project)

def test_get_theme_preference(project_context):
    assert project_context.get_theme_preference() in ['light', 'dark']

def test_set_theme_preference(project_context):
    initial_theme = project_context.get_theme_preference()
    new_theme = 'dark' if initial_theme == 'light' else 'light'
    project_context.set_theme_preference(new_theme)
    assert project_context.get_theme_preference() == new_theme

def test_theme_preference_persistence(project_context):
    initial_theme = project_context.get_theme_preference()
    new_theme = 'dark' if initial_theme == 'light' else 'light'
    project_context.set_theme_preference(new_theme)
    project_context.save_settings()
    reloaded_context = ProjectContext(project_context.project)
    assert reloaded_context.get_theme_preference() == new_theme

def test_theme_preference_invalid_value(project_context):
    with pytest.raises(ValueError):
        project_context.set_theme_preference('invalid_theme')

def test_theme_preference_change_signal(project_context, qtbot):
    with qtbot.waitSignal(project_context.theme_changed, timeout=1000) as blocker:
        project_context.set_theme_preference('dark' if project_context.get_theme_preference() == 'light' else 'light')
    assert blocker.signal_triggered

def test_is_initialized(project_context):
    assert project_context.is_initialized

def test_not_initialized(mock_project):
    incomplete_context = ProjectContext(mock_project)
    incomplete_context.settings_manager = None
    assert not incomplete_context.is_initialized

def test_project_context_with_theme_manager(project_context):
    assert isinstance(project_context.theme_manager, ThemeManager)

def test_theme_manager_singleton(project_context):
    assert project_context.theme_manager is ThemeManager.get_instance()

def test_initialize_auto_exclude_manager(project_context):
    project_context.initialize_auto_exclude_manager()
    assert isinstance(project_context.auto_exclude_manager, AutoExcludeManager)

def test_initialize_directory_analyzer(project_context):
    project_context.initialize_directory_analyzer()
    assert isinstance(project_context.directory_analyzer, DirectoryAnalyzer)

def test_detect_project_types_multiple(project_context, tmpdir):
    tmpdir.join("main.py").write("print('Hello, World!')")
    tmpdir.join("index.html").write("<html><body>Hello, World!</body></html>")
    tmpdir.join("package.json").write('{"name": "test-project", "version": "1.0.0"}')
    project_context.detect_project_types()
    assert 'python' in project_context.project_types
    assert 'web' in project_context.project_types
    assert 'javascript' in project_context.project_types

def test_get_all_exclusions(project_context):
    exclusions = project_context.settings_manager.get_all_exclusions()
    assert 'root_exclusions' in exclusions
    assert 'excluded_dirs' in exclusions
    assert 'excluded_files' in exclusions

def test_update_settings(project_context):
    new_settings = {
        'root_exclusions': ['new_root'],
        'excluded_dirs': ['new_dir'],
        'excluded_files': ['new_file.txt']
    }
    project_context.settings_manager.update_settings(new_settings)
    updated_exclusions = project_context.settings_manager.get_all_exclusions()
    assert 'new_root' in updated_exclusions['root_exclusions']
    assert 'new_dir' in updated_exclusions['excluded_dirs']
    assert 'new_file.txt' in updated_exclusions['excluded_files']

def test_project_context_serialization(project_context):
    serialized = project_context.to_dict()
    assert 'name' in serialized
    assert 'start_directory' in serialized
    assert 'root_exclusions' in serialized
    assert 'excluded_dirs' in serialized
    assert 'excluded_files' in serialized
    assert 'theme_preference' in serialized

def test_project_context_deserialization(mock_project):
    data = {
        'name': 'test_project',
        'start_directory': '/test/path',
        'root_exclusions': ['root1', 'root2'],
        'excluded_dirs': ['dir1', 'dir2'],
        'excluded_files': ['file1.txt', 'file2.txt'],
        'theme_preference': 'dark'
    }
    context = ProjectContext.from_dict(data)
    assert context.project.name == 'test_project'
    assert context.project.start_directory == '/test/path'
    assert set(context.settings_manager.get_root_exclusions()) == set(['root1', 'root2'])
    assert set(context.settings_manager.get_excluded_dirs()) == set(['dir1', 'dir2'])
    assert set(context.settings_manager.get_excluded_files()) == set(['file1.txt', 'file2.txt'])
    assert context.get_theme_preference() == 'dark'