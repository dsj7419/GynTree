import json
import pytest
import os
import logging
import gc
import psutil
from pathlib import Path
from typing import Dict, Any, Generator
from contextlib import contextmanager

from services.ProjectContext import ProjectContext
from models.Project import Project
from services.SettingsManager import SettingsManager
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.auto_exclude.AutoExcludeManager import AutoExcludeManager
from services.RootExclusionManager import RootExclusionManager
from services.ProjectTypeDetector import ProjectTypeDetector
from utilities.theme_manager import ThemeManager

pytestmark = pytest.mark.integration

logger = logging.getLogger(__name__)

class ProjectContextTestHelper:
    def __init__(self, tmpdir: Path):
        self.tmpdir = tmpdir
        self.initial_memory = None
        self.context = None

    def setup_project_files(self, project_type: str) -> None:
        if project_type == "python":
            (self.tmpdir / "main.py").write_text("print('hello, world!')", encoding='utf-8')
            (self.tmpdir / "requirements.txt").write_text("pytest\nPyQt5", encoding='utf-8')
        elif project_type == "web":
            (self.tmpdir / "index.html").write_text("<html><body>Hello!</body></html>", encoding='utf-8')
        elif project_type == "javascript":
            (self.tmpdir / "package.json").write_text('{"name": "test"}', encoding='utf-8')
            (self.tmpdir / "index.js").write_text("console.log('hello')", encoding='utf-8')

    def create_project(self, name: str = "test_project") -> Project:
        return Project(
            name=name,
            start_directory=str(self.tmpdir),
            root_exclusions=[],
            excluded_dirs=[],
            excluded_files=[]
        )

    def track_memory(self) -> None:
        gc.collect()
        self.initial_memory = psutil.Process().memory_info().rss

    def check_memory_usage(self, operation: str) -> None:
        if self.initial_memory is not None:
            gc.collect()
            current_memory = psutil.Process().memory_info().rss
            memory_diff = current_memory - self.initial_memory
            if memory_diff > 50 * 1024 * 1024:
                logger.warning(f"High memory usage after {operation}: {memory_diff / 1024 / 1024:.2f}MB")

@pytest.fixture
def helper(tmpdir) -> ProjectContextTestHelper:
    return ProjectContextTestHelper(Path(tmpdir))

@pytest.fixture
def mock_project(helper) -> Project:
    return helper.create_project()

@pytest.fixture
def project_context(mock_project: Project) -> Generator[ProjectContext, None, None]:
    context = ProjectContext(mock_project)
    context.initialize()
    yield context
    context.close()
    gc.collect()
    
@pytest.mark.timeout(30)
def test_initialization(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    assert project_context.project is not None
    assert isinstance(project_context.settings_manager, SettingsManager)
    assert isinstance(project_context.directory_analyzer, DirectoryAnalyzer)
    assert isinstance(project_context.auto_exclude_manager, AutoExcludeManager)
    assert isinstance(project_context.root_exclusion_manager, RootExclusionManager)
    assert isinstance(project_context.project_type_detector, ProjectTypeDetector)
    
    helper.check_memory_usage("initialization")

@pytest.mark.timeout(30)
def test_detect_project_types(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    helper.setup_project_files("python")
    helper.setup_project_files("web")
    
    project_context.project_type_detector = ProjectTypeDetector(str(helper.tmpdir))
    project_context.detect_project_types()
    
    assert 'python' in project_context.project_types
    assert 'web' in project_context.project_types
    
    helper.check_memory_usage("project type detection")

@pytest.mark.timeout(30)
def test_initialize_root_exclusions(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    initial_exclusions = set(project_context.settings_manager.get_root_exclusions())
    project_context.initialize_root_exclusions()
    updated_exclusions = set(project_context.settings_manager.get_root_exclusions())
    
    assert updated_exclusions >= initial_exclusions
    helper.check_memory_usage("root exclusions initialization")

@pytest.mark.timeout(30)
def test_trigger_auto_exclude(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    result = project_context.trigger_auto_exclude()
    assert isinstance(result, str)
    assert len(result) > 0
    
    helper.check_memory_usage("auto-exclude")

@pytest.mark.timeout(30)
def test_get_directory_tree(project_context: ProjectContext, helper: ProjectContextTestHelper, tmpdir: Path) -> None:
    helper.track_memory()
    
    test_dir = Path(tmpdir)
    test_file = test_dir / "test_file.py"
    nested_dir = test_dir / "nested_dir"  # Changed from test_dir to avoid auto-exclusion
    nested_file = nested_dir / "nested_file.txt"
    
    test_file.write_text("# test content", encoding='utf-8')
    nested_dir.mkdir(exist_ok=True)
    nested_file.write_text("nested content", encoding='utf-8')
    
    # Clear any existing exclusions
    project_context.settings_manager.excluded_dirs = []
    
    tree = project_context.get_directory_tree()
    
    assert isinstance(tree, dict)
    assert tree['type'] == 'directory'
    assert any(child['name'] == test_file.name for child in tree['children'])
    assert any(child['name'] == nested_dir.name for child in tree['children'])
    
    helper.check_memory_usage("directory tree generation")

@pytest.mark.timeout(30)
def test_save_settings(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    # Configure project_dir to ensure settings are saved in the right place
    project_dir = helper.tmpdir
    settings_dir = project_dir / "config" / "projects"
    settings_dir.mkdir(parents=True, exist_ok=True)
    
    # Update start directory to point to our test directory
    project_context.project.start_directory = str(project_dir)
    
    # Add excluded directory and save
    project_context.settings_manager.add_excluded_dir("test_dir")
    project_context.save_settings()
    
    project_context.settings_manager.load_settings()  # Force reload settings
    excluded_dirs = project_context.settings_manager.get_excluded_dirs()
    assert "test_dir" in excluded_dirs
    
    helper.check_memory_usage("settings persistence")

@pytest.mark.timeout(30)
def test_close(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    project_context.close()
    
    assert project_context.settings_manager is None
    assert project_context.directory_analyzer is None
    assert project_context.auto_exclude_manager is None
    assert len(project_context.project_types) == 0
    assert project_context.project_type_detector is None
    
    helper.check_memory_usage("context cleanup")

@pytest.mark.timeout(30)
def test_project_context_with_existing_settings(mock_project: Project, helper: ProjectContextTestHelper, tmpdir: Path) -> None:
    helper.track_memory()
    
    # Create project directory with settings
    project_dir = helper.tmpdir
    project_dir.mkdir(exist_ok=True)
    
    # Create settings directory in project directory
    settings_dir = project_dir / "config" / "projects"
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_file = settings_dir / f"{mock_project.name}.json"
    
    settings_data = {
        "root_exclusions": ["existing_root"],
        "excluded_dirs": ["existing_dir"],
        "excluded_files": ["existing_file"],
        "theme_preference": "dark"
    }
    
    # Ensure settings file is properly written with newline
    settings_file.write_text(json.dumps(settings_data, indent=4) + "\n", encoding='utf-8')
    
    # Set up project with existing settings
    mock_project.start_directory = str(project_dir)
    mock_project.root_exclusions = ["existing_root"] 
    mock_project.excluded_dirs = ["existing_dir"]
    mock_project.excluded_files = ["existing_file"]
    
    # Create context and initialize before loading settings
    context = ProjectContext(mock_project)
    context.initialize()
    
    try:
        # Get theme directly from settings file to verify
        assert context.get_theme_preference() == "dark"
        
        root_exclusions = context.settings_manager.get_root_exclusions()
        excluded_dirs = context.settings_manager.get_excluded_dirs()
        excluded_files = context.settings_manager.get_excluded_files()
        
        assert "existing_root" in root_exclusions
        assert "existing_dir" in excluded_dirs
        assert "existing_file" in excluded_files
    finally:
        context.close()
    
    helper.check_memory_usage("existing settings")

@pytest.mark.timeout(30)
def test_theme_management(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    initial_theme = project_context.get_theme_preference()
    new_theme = 'dark' if initial_theme == 'light' else 'light'
    
    project_context.set_theme_preference(new_theme)
    assert project_context.get_theme_preference() == new_theme
    
    project_context.save_settings()
    
    new_context = ProjectContext(project_context.project)
    new_context.initialize()
    try:
        assert new_context.get_theme_preference() == new_theme
    finally:
        new_context.close()
    
    helper.check_memory_usage("theme management")

@pytest.mark.timeout(30)
def test_project_type_detection_multiple(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    helper.setup_project_files("python")
    helper.setup_project_files("javascript")
    helper.setup_project_files("web")
    
    project_context.project_type_detector = ProjectTypeDetector(str(helper.tmpdir))
    project_context.detect_project_types()
    
    assert 'python' in project_context.project_types
    assert 'javascript' in project_context.project_types
    assert 'web' in project_context.project_types
    
    helper.check_memory_usage("multiple project type detection")

@pytest.mark.timeout(30)
def test_auto_exclude_manager_initialization(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    project_context.initialize_auto_exclude_manager()
    assert isinstance(project_context.auto_exclude_manager, AutoExcludeManager)
    
    original_manager = project_context.auto_exclude_manager
    project_context.initialize_auto_exclude_manager()
    assert project_context.auto_exclude_manager is not original_manager
    
    helper.check_memory_usage("auto-exclude manager initialization")

@pytest.mark.timeout(30)
def test_directory_analyzer_reinitialize(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    original_analyzer = project_context.directory_analyzer
    project_context.reinitialize_directory_analyzer()
    assert project_context.directory_analyzer is not original_analyzer
    assert isinstance(project_context.directory_analyzer, DirectoryAnalyzer)
    
    helper.check_memory_usage("directory analyzer reinitialization")

@pytest.mark.timeout(30)
def test_error_handling(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    with pytest.raises(ValueError):
        project_context.set_theme_preference('invalid_theme')
    
    project_context.settings_manager = None
    result = project_context.trigger_auto_exclude()
    assert result == "Project context not initialized"
    
    helper.check_memory_usage("error handling")

@pytest.mark.timeout(30)
def test_context_serialization(project_context: ProjectContext, helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    project_context.settings_manager.add_excluded_dir("test_dir")
    project_context.set_theme_preference("dark")
    project_context.save_settings()
    
    new_context = ProjectContext(project_context.project)
    new_context.initialize()
    try:
        assert "test_dir" in new_context.settings_manager.get_excluded_dirs()
        assert new_context.get_theme_preference() == "dark"
    finally:
        new_context.close()
    
    helper.check_memory_usage("context serialization")

@pytest.mark.timeout(30)
def test_cleanup_on_exception(helper: ProjectContextTestHelper) -> None:
    helper.track_memory()
    
    # Create a project with a directory that exists
    test_dir = helper.tmpdir / "initial_dir"
    test_dir.mkdir(exist_ok=True)
    
    mock_project = helper.create_project()
    mock_project.start_directory = str(test_dir)
    
    context = ProjectContext(mock_project)
    context.initialize()
    
    try:
        # Remove directory after initial initialization
        test_dir.rmdir()
        
        # Should fail when trying to reinitialize
        with pytest.raises(ValueError, match="Project directory does not exist"):
            context.reinitialize_directory_analyzer()
            
        # Verify cleanup occurred - context should be deactivated
        assert not context._is_active
        assert context.settings_manager is None
        assert context.directory_analyzer is None
        
    finally:
        if context:
            try:
                context.close()
            except:
                pass
    
    helper.check_memory_usage("cleanup on exception")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])