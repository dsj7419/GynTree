import pytest
from services.auto_exclude.AutoExcludeManager import AutoExcludeManager
from services.SettingsManager import SettingsManager
from services.ProjectTypeDetector import ProjectTypeDetector
from models.Project import Project

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
def settings_manager(mock_project):
    return SettingsManager(mock_project)

@pytest.fixture
def project_type_detector(mock_project):
    return ProjectTypeDetector(mock_project.start_directory)

@pytest.fixture
def auto_exclude_manager(mock_project, settings_manager, project_type_detector):
    return AutoExcludeManager(mock_project.start_directory, settings_manager, set(), project_type_detector)

def test_initialization(auto_exclude_manager):
    assert auto_exclude_manager.start_directory is not None
    assert isinstance(auto_exclude_manager.settings_manager, SettingsManager)
    assert isinstance(auto_exclude_manager.project_types, set)
    assert len(auto_exclude_manager.exclusion_services) > 0

def test_get_recommendations(auto_exclude_manager):
    recommendations = auto_exclude_manager.get_recommendations()
    assert 'root_exclusions' in recommendations
    assert 'excluded_dirs' in recommendations
    assert 'excluded_files' in recommendations

def test_get_formatted_recommendations(auto_exclude_manager):
    formatted_recommendations = auto_exclude_manager.get_formatted_recommendations()
    assert isinstance(formatted_recommendations, str)
    assert "Root Exclusions:" in formatted_recommendations
    assert "Excluded Dirs:" in formatted_recommendations
    assert "Excluded Files:" in formatted_recommendations

def test_apply_recommendations(auto_exclude_manager, settings_manager):
    initial_settings = settings_manager.get_all_exclusions()
    auto_exclude_manager.apply_recommendations()
    updated_settings = settings_manager.get_all_exclusions()
    assert updated_settings != initial_settings

def test_project_type_detection(tmpdir, settings_manager, project_type_detector):
    tmpdir.join("main.py").write("print('Hello, World!')")
    tmpdir.join("requirements.txt").write("pytest\npyqt5")
    detected_types = project_type_detector.detect_project_types()
    project_types = {ptype for ptype, detected in detected_types.items() if detected}
    manager = AutoExcludeManager(str(tmpdir), settings_manager, project_types, project_type_detector)
    assert 'python' in manager.project_types

def test_exclusion_services_creation(tmpdir, settings_manager, project_type_detector):
    tmpdir.join("main.py").write("print('Hello, World!')")
    tmpdir.join("index.html").write("<html></html>")
    detected_types = project_type_detector.detect_project_types()
    project_types = {ptype for ptype, detected in detected_types.items() if detected}
    auto_exclude_manager = AutoExcludeManager(str(tmpdir), settings_manager, project_types, project_type_detector)
    service_names = [service.__class__.__name__ for service in auto_exclude_manager.exclusion_services]
    assert 'IDEAndGitAutoExclude' in service_names
    assert 'PythonAutoExclude' in service_names
    assert 'WebAutoExclude' in service_names

def test_new_exclusions_after_settings_update(auto_exclude_manager, settings_manager):
    initial_recommendations = auto_exclude_manager.get_recommendations()
    settings_manager.update_settings({
        'root_exclusions': list(initial_recommendations['root_exclusions']),
        'excluded_dirs': list(initial_recommendations['excluded_dirs']),
        'excluded_files': list(initial_recommendations['excluded_files'])
    })
    new_recommendations = auto_exclude_manager.get_recommendations()
    assert new_recommendations != initial_recommendations

def test_invalid_settings_key_handling(auto_exclude_manager, settings_manager):
    initial_settings = settings_manager.get_all_exclusions()
    auto_exclude_manager.apply_recommendations()
    # Try to update with an invalid key
    settings_manager.update_settings({'invalid_key': ['some_value']})
    updated_settings = settings_manager.get_all_exclusions()
    assert 'invalid_key' not in updated_settings
    assert updated_settings != initial_settings