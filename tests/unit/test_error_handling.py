import os
import time
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox

from controllers.AppController import AppController
from controllers.ProjectController import ProjectController
from models.Project import Project
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.ProjectContext import ProjectContext


@pytest.fixture
def app():
    return QApplication([])


@pytest.fixture
def mock_settings():
    settings = Mock()
    settings.get_root_exclusions.return_value = []
    settings.get_excluded_dirs.return_value = []
    settings.get_excluded_files.return_value = []
    settings.is_excluded.return_value = False
    return settings


@pytest.fixture
def mock_project():
    project = Mock(spec=Project)
    project.name = "test_project"
    project.start_directory = "/test/path"
    project.root_exclusions = []
    project.excluded_dirs = []
    project.excluded_files = []
    with patch.object(Project, "_validate_directory"):
        return project


class TestErrorHandling:
    def test_directory_analyzer_permission_denied(self, mock_settings):
        with patch("os.access", return_value=False), patch(
            "os.path.exists", return_value=True
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "services.DirectoryStructureService.DirectoryStructureService.get_hierarchical_structure"
        ) as mock_struct:
            mock_struct.return_value = {
                "error": "Permission denied: /test/path",
                "children": [],
                "name": "path",
                "path": "/test/path",
            }
            analyzer = DirectoryAnalyzer("/test/path", mock_settings)
            result = analyzer.analyze_directory()
            assert result.get("error") is not None
            assert "permission denied" in str(result.get("error")).lower()

    def test_directory_analyzer_nonexistent_path(self, mock_settings):
        analyzer = DirectoryAnalyzer("/nonexistent/path", mock_settings)
        result = analyzer.analyze_directory()
        assert result.get("error") is not None
        assert "exist" in str(result.get("error")).lower()

    def test_project_context_invalid_initialization(self, mock_project):
        context = ProjectContext(mock_project)
        with patch("pathlib.Path.exists", return_value=False), patch(
            "PyQt5.QtWidgets.QMessageBox.critical"
        ) as mock_message:
            with pytest.raises(ValueError):
                context.initialize()
            assert not context._is_active
            assert context.settings_manager is None
            mock_message.assert_not_called()

    def test_project_context_cleanup_after_error(self, mock_project):
        context = ProjectContext(mock_project)
        with patch.object(
            context, "initialize", side_effect=Exception("Test error")
        ), patch("PyQt5.QtWidgets.QMessageBox.critical"):
            try:
                context.initialize()
            except Exception:
                pass
            assert not context._is_active
            assert context.settings_manager is None
            assert context.directory_analyzer is None

    def test_app_controller_error_handling(self):
        # Test setup
        controller = AppController()
        with patch("PyQt5.QtWidgets.QMessageBox.critical") as mock_message:
            controller.thread_controller.worker_error.emit("Test error")
            time.sleep(0.5)  # Allow time for the thread to handle the error
            mock_message.assert_called_once()

    def test_analyzer_stop_on_error(self, mock_settings):
        analyzer = DirectoryAnalyzer("/test/path", mock_settings)
        with patch("os.walk", side_effect=PermissionError), patch(
            "PyQt5.QtWidgets.QMessageBox.critical"
        ), patch(
            "services.DirectoryStructureService.DirectoryStructureService.get_hierarchical_structure"
        ) as mock_struct:
            mock_struct.return_value = {"error": "Access error", "children": []}
            result = analyzer.analyze_directory()
            assert result.get("error") is not None
            assert not analyzer._stop_event.is_set()

    def test_project_context_error_recovery(self, mock_project):
        context = ProjectContext(mock_project)
        context.auto_exclude_manager = None

        with patch("pathlib.Path.exists", return_value=True), patch(
            "PyQt5.QtWidgets.QMessageBox.critical"
        ), patch.object(context, "settings_manager", Mock()), patch.object(
            ProjectContext, "trigger_auto_exclude", side_effect=Exception("Test error")
        ):
            try:
                result = context.trigger_auto_exclude()
            except Exception as e:
                assert "error" in str(e).lower()

    def test_settings_manager_error_handling(self, mock_project):
        context = ProjectContext(mock_project)
        with patch("pathlib.Path.exists", return_value=False), patch(
            "PyQt5.QtWidgets.QMessageBox.critical"
        ):
            try:
                context.initialize()
            except ValueError:
                pass
            assert not context._is_active
            assert context.settings_manager is None

    def test_directory_analyzer_unicode_error(self, mock_settings):
        analyzer = DirectoryAnalyzer("/test/path", mock_settings)
        with patch("os.walk", return_value=[(None, [], ["test\udcff.txt"])]), patch(
            "os.path.exists", return_value=True
        ), patch("pathlib.Path.exists", return_value=True), patch(
            "PyQt5.QtWidgets.QMessageBox.critical"
        ):
            result = analyzer.analyze_directory()
            assert result is not None
            assert "children" in result
