# GynTree: This file configures the test environment for pytest. It adds the src directory to the Python path so that the tests can access the main modules.
import sys
import os
import pytest
from PyQt5.QtWidgets import QApplication
import psutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from models.Project import Project
from services.SettingsManager import SettingsManager
from services.ProjectTypeDetector import ProjectTypeDetector
from services.ProjectContext import ProjectContext

@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the entire test session."""
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def mock_project(tmpdir):
    """Create a mock Project instance for testing."""
    return Project(
        name="test_project",
        start_directory=str(tmpdir),
        root_exclusions=["node_modules"],
        excluded_dirs=["dist"],
        excluded_files=[".env"]
    )

@pytest.fixture
def settings_manager(mock_project, tmpdir):
    """Create a SettingsManager instance for testing."""
    SettingsManager.config_dir = str(tmpdir.mkdir("config"))
    return SettingsManager(mock_project)

@pytest.fixture
def project_type_detector(tmpdir):
    """Create a ProjectTypeDetector instance for testing."""
    return ProjectTypeDetector(str(tmpdir))

@pytest.fixture
def project_context(mock_project):
    """Create a ProjectContext instance for testing."""
    return ProjectContext(mock_project)

@pytest.fixture
def setup_python_project(tmpdir):
    """Set up a basic Python project structure for testing."""
    tmpdir.join("main.py").write("print('Hello, World!')")
    tmpdir.join("requirements.txt").write("pytest\npyqt5")
    return tmpdir

@pytest.fixture
def setup_web_project(tmpdir):
    """Set up a basic web project structure for testing."""
    tmpdir.join("index.html").write("<html><body>Hello, World!</body></html>")
    tmpdir.join("styles.css").write("body { font-family: Arial, sans-serif; }")
    return tmpdir

@pytest.fixture
def setup_complex_project(tmpdir):
    """Set up a complex project structure with multiple project types for testing."""
    tmpdir.join("main.py").write("print('Hello, World!')")
    tmpdir.join("package.json").write('{"name": "test-project", "version": "1.0.0"}')
    tmpdir.mkdir("src").join("app.js").write("console.log('Hello, World!');")
    tmpdir.mkdir("public").join("index.html").write("<html><body>Hello, World!</body></html>")
    tmpdir.mkdir("migrations")
    return tmpdir

@pytest.fixture
def create_large_directory_structure(tmpdir):
    def _create_large_directory_structure(depth=5, files_per_dir=100):
        def create_files(directory, num_files):
            for i in range(num_files):
                file_path = os.path.join(directory, f"file_{i}.txt")
                with open(file_path, 'w') as f:
                    f.write(f"# gyntree: Test file {i}")

        def create_dirs(root, current_depth):
            if current_depth > depth:
                return
            create_files(root, files_per_dir)
            for i in range(5):  # Create 5 subdirectories
                subdir = os.path.join(root, f"dir_{i}")
                os.mkdir(subdir)
                create_dirs(subdir, current_depth + 1)

        create_dirs(str(tmpdir), 1)
        return tmpdir

    return _create_large_directory_structure

def pytest_configure(config):
    """Add custom markers to the pytest configuration."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "gui: marks tests that require a GUI (deselect with '-m \"not gui\"')")
    config.addinivalue_line("markers", "memory: marks tests that perform memory profiling")