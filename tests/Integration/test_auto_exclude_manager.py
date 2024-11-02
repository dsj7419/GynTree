# tests/Integration/test_auto_exclude_manager.py

import pytest
import os
import logging
import gc
import psutil
from pathlib import Path
from typing import Set, Dict, Any

from services.auto_exclude.AutoExcludeManager import AutoExcludeManager
from services.SettingsManager import SettingsManager
from services.ProjectTypeDetector import ProjectTypeDetector
from models.Project import Project

pytestmark = pytest.mark.integration

logger = logging.getLogger(__name__)

class AutoExcludeTestHelper:
    """Helper class for AutoExcludeManager testing"""
    def __init__(self, tmpdir: Path):
        self.tmpdir = tmpdir
        self.initial_memory = None

    def create_test_structure(self, project_type: str) -> None:
        """Create test project structure"""
        if project_type == "python":
            (self.tmpdir / "main.py").write_text("print('Hello, World!')")
            (self.tmpdir / "requirements.txt").write_text("pytest\nPyQt5")
            (self.tmpdir / "tests").mkdir(exist_ok=True)
            (self.tmpdir / "__pycache__").mkdir(exist_ok=True)
        elif project_type == "javascript":
            (self.tmpdir / "package.json").write_text('{"name": "test"}')
            (self.tmpdir / "index.js").write_text("console.log('hello')")
            (self.tmpdir / "node_modules").mkdir(exist_ok=True)
        elif project_type == "web":
            (self.tmpdir / "index.html").write_text("<html></html>")
            (self.tmpdir / "styles.css").write_text("body {}")
            (self.tmpdir / "dist").mkdir(exist_ok=True)

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
                logger.warning(f"High memory usage after {operation}: {memory_diff / 1024 / 1024:.2f}MB")

@pytest.fixture
def helper(tmpdir):
    """Create test helper instance"""
    return AutoExcludeTestHelper(Path(tmpdir))

@pytest.fixture
def mock_project(helper):
    """Create mock project instance"""
    return Project(
        name="test_project",
        start_directory=str(helper.tmpdir),
        root_exclusions=[],
        excluded_dirs=[],
        excluded_files=[]
    )

@pytest.fixture
def settings_manager(mock_project):
    """Create SettingsManager instance"""
    return SettingsManager(mock_project)

@pytest.fixture
def project_type_detector(mock_project):
    """Create ProjectTypeDetector instance"""
    return ProjectTypeDetector(mock_project.start_directory)

@pytest.fixture
def auto_exclude_manager(mock_project, settings_manager, project_type_detector):
    """Create AutoExcludeManager instance"""
    manager = AutoExcludeManager(
        mock_project.start_directory,
        settings_manager,
        set(),
        project_type_detector
    )
    yield manager
    gc.collect()

@pytest.mark.timeout(30)
def test_initialization(auto_exclude_manager, helper):
    """Test initial setup of AutoExcludeManager"""
    helper.track_memory()
    assert auto_exclude_manager.start_directory is not None
    assert isinstance(auto_exclude_manager.settings_manager, SettingsManager)
    assert isinstance(auto_exclude_manager.project_types, set)
    assert len(auto_exclude_manager.exclusion_services) > 0
    helper.check_memory_usage("initialization")

@pytest.mark.timeout(30)
def test_get_recommendations(auto_exclude_manager, helper):
    """Test recommendations retrieval"""
    helper.track_memory()
    recommendations = auto_exclude_manager.get_recommendations()
    assert isinstance(recommendations, dict)
    assert 'root_exclusions' in recommendations
    assert 'excluded_dirs' in recommendations
    assert 'excluded_files' in recommendations
    helper.check_memory_usage("get recommendations")

@pytest.mark.timeout(30)
def test_get_formatted_recommendations(helper, settings_manager, project_type_detector):
    """Test formatted recommendations output"""
    helper.track_memory()
    helper.create_test_structure("web")
    settings_manager.update_settings({
        'root_exclusions': [],
        'excluded_dirs': [],
        'excluded_files': []
    })
    detected_types = project_type_detector.detect_project_types()
    project_types = {ptype for ptype, detected in detected_types.items() if detected}
    auto_exclude_manager = AutoExcludeManager(
        str(helper.tmpdir),
        settings_manager,
        project_types,
        project_type_detector
    )
    formatted = auto_exclude_manager.get_formatted_recommendations()
    assert isinstance(formatted, str)
    assert "Root Exclusions:" in formatted
    assert "Excluded Dirs:" in formatted
    assert "Excluded Files:" in formatted
    helper.check_memory_usage("format recommendations")

@pytest.mark.timeout(30)
def test_apply_recommendations(auto_exclude_manager, settings_manager, helper):
    """Test applying recommendations to settings"""
    helper.track_memory()
    settings_manager.update_settings({
        'root_exclusions': [],
        'excluded_dirs': [],
        'excluded_files': []
    })
    initial_settings = settings_manager.get_all_exclusions()
    auto_exclude_manager.apply_recommendations()
    updated_settings = settings_manager.get_all_exclusions()
    assert updated_settings != initial_settings
    assert len(updated_settings['root_exclusions']) >= len(initial_settings['root_exclusions'])
    helper.check_memory_usage("apply recommendations")

@pytest.mark.timeout(30)
def test_project_type_detection(helper, settings_manager, project_type_detector):
    """Test project type detection and recommendations"""
    helper.track_memory()
    helper.create_test_structure("python")
    detected_types = project_type_detector.detect_project_types()
    project_types = {ptype for ptype, detected in detected_types.items() if detected}
    manager = AutoExcludeManager(
        str(helper.tmpdir),
        settings_manager,
        project_types,
        project_type_detector
    )
    assert 'python' in manager.project_types
    recommendations = manager.get_recommendations()
    assert '__pycache__' in recommendations['root_exclusions']
    helper.check_memory_usage("type detection")

@pytest.mark.timeout(30)
def test_exclusion_services_creation(helper, settings_manager, project_type_detector):
    """Test creation of appropriate exclusion services"""
    helper.track_memory()
    helper.create_test_structure("python")
    helper.create_test_structure("web")
    detected_types = project_type_detector.detect_project_types()
    project_types = {ptype for ptype, detected in detected_types.items() if detected}
    manager = AutoExcludeManager(
        str(helper.tmpdir),
        settings_manager,
        project_types,
        project_type_detector
    )
    service_names = [service.__class__.__name__ for service in manager.exclusion_services]
    assert 'IDEandGitAutoExclude' in service_names
    assert 'PythonAutoExclude' in service_names
    assert 'WebAutoExclude' in service_names
    helper.check_memory_usage("services creation")

@pytest.mark.timeout(30)
def test_new_exclusions_after_settings_update(auto_exclude_manager, settings_manager, helper):
    """Test recommendation updates after settings changes"""
    helper.track_memory()
    initial_recommendations = auto_exclude_manager.get_recommendations()
    settings_manager.update_settings({
        'root_exclusions': list(initial_recommendations['root_exclusions']),
        'excluded_dirs': list(initial_recommendations['excluded_dirs']),
        'excluded_files': list(initial_recommendations['excluded_files'])
    })
    new_recommendations = auto_exclude_manager.get_recommendations()
    assert new_recommendations != initial_recommendations
    helper.check_memory_usage("settings update")

@pytest.mark.timeout(30)
def test_invalid_settings_key_handling(auto_exclude_manager, settings_manager, helper):
    """Test handling of invalid settings keys"""
    helper.track_memory()
    initial_settings = settings_manager.get_all_exclusions()
    auto_exclude_manager.apply_recommendations()
    settings_manager.update_settings({'invalid_key': ['some_value']})
    updated_settings = settings_manager.get_all_exclusions()
    assert 'invalid_key' not in updated_settings
    assert updated_settings == settings_manager.get_all_exclusions()
    helper.check_memory_usage("invalid settings")

@pytest.mark.timeout(30)
def test_multiple_project_types(helper, settings_manager, project_type_detector):
    """Test handling of multiple project types"""
    helper.track_memory()
    helper.create_test_structure("python")
    helper.create_test_structure("javascript")
    helper.create_test_structure("web")
    detected_types = project_type_detector.detect_project_types()
    project_types = {ptype for ptype, detected in detected_types.items() if detected}
    manager = AutoExcludeManager(
        str(helper.tmpdir),
        settings_manager,
        project_types,
        project_type_detector
    )
    recommendations = manager.get_recommendations()
    assert '__pycache__' in recommendations['root_exclusions']
    assert 'node_modules' in recommendations['root_exclusions']
    assert 'dist' in recommendations['root_exclusions']
    helper.check_memory_usage("multiple types")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
