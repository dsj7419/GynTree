import gc
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
import pytest
from PyQt5.QtCore import QPoint, QSize, Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QWidget,
)

from components.UI.animated_toggle import AnimatedToggle
from components.UI.AutoExcludeUI import AutoExcludeUI
from components.UI.DashboardUI import DashboardUI
from components.UI.DirectoryTreeUI import DirectoryTreeUI
from components.UI.ExclusionsManagerUI import ExclusionsManagerUI
from components.UI.ProjectUI import ProjectUI
from components.UI.ResultUI import ResultUI
from utilities.theme_manager import ThemeManager

pytestmark = [pytest.mark.functional, pytest.mark.gui]

logger = logging.getLogger(__name__)


class MockController:
    def __init__(self):
        self.project_controller = MockProjectController()
        self.theme_manager = ThemeManager.getInstance()
        self.manage_projects = lambda: None
        self.manage_exclusions = lambda: None
        self.analyze_directory = lambda: None
        self.view_directory_tree = lambda: None
        self.on_project_created = self._on_project_created
        self.on_project_loaded = self._on_project_loaded
        self.project_context = None
        self.main_ui = None

    def _on_project_created(self, project):
        try:
            success = self.project_controller.create_project(project)
            if success:
                self.project_context = self.project_controller.project_context
                if self.main_ui:
                    self.main_ui.update_project_info(project)
                    self.main_ui.enable_project_actions()
        except Exception as e:
            QMessageBox.critical(
                self.main_ui, "Error", f"An unexpected error occurred: {str(e)}"
            )
            raise

    def _on_project_loaded(self, project):
        try:
            success = self.project_controller.load_project(project)
            if success:
                self.project_context = self.project_controller.project_context
                if self.main_ui:
                    self.main_ui.update_project_info(project)
                    self.main_ui.enable_project_actions()
        except Exception as e:
            QMessageBox.critical(
                self.main_ui, "Error", f"An unexpected error occurred: {str(e)}"
            )


class MockProjectController:
    def __init__(self):
        self.project_context = None
        self.current_project = None
        self.is_project_loaded = False

    def create_project(self, project):
        try:
            self.current_project = project
            self.project_context = MockProjectContext()
            self.is_project_loaded = True
            return True
        except Exception:
            self.is_project_loaded = False
            self.project_context = None
            self.current_project = None
            raise

    def close_project(self):
        self.project_context = None
        self.current_project = None
        self.is_project_loaded = False

    def get_theme_preference(self):
        return "light"

    def set_theme_preference(self, theme):
        pass

    def load_project(self, project):
        try:
            self.current_project = project
            self.project_context = MockProjectContext()
            self.is_project_loaded = True
            return True
        except Exception:
            self.is_project_loaded = False
            self.project_context = None
            self.current_project = None
            return False


class MockUI:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    def deleteLater(self):
        pass


class MockAutoExcludeUI(MockUI):
    pass


class MockResultUI(MockUI):
    pass


class MockDirectoryTreeUI(MockUI):
    pass


class MockProjectContext:
    def __init__(self):
        self.is_initialized = True
        self.auto_exclude_manager = MockAutoExcludeManager()
        self.settings_manager = MockSettingsManager()
        self.directory_analyzer = MockDirectoryAnalyzer()

    def close(self):
        pass

    def get_theme_preference(self):
        return "light"

    def set_theme_preference(self, theme):
        pass


class MockAutoExcludeManager:
    def has_new_recommendations(self):
        return True

    def get_recommendations(self):
        return {
            "root_exclusions": set(),
            "excluded_dirs": set(),
            "excluded_files": set(),
        }


class MockSettingsManager:
    def get_root_exclusions(self):
        return []

    def get_excluded_dirs(self):
        return []

    def get_excluded_files(self):
        return []

    def get_theme_preference(self):
        return "light"

    def get_all_exclusions(self):
        return {"root_exclusions": [], "excluded_dirs": [], "excluded_files": []}


class MockDirectoryAnalyzer:
    def get_directory_tree(self):
        return {"name": "root", "type": "directory", "children": []}


class DashboardTestHelper:
    def __init__(self):
        self.initial_memory = None
        self.default_project = {
            "name": "test_project",
            "start_directory": "/test/path",
            "status": "Test Project Status",
        }

    def track_memory(self) -> None:
        gc.collect()
        self.initial_memory = psutil.Process().memory_info().rss

    def check_memory_usage(self, operation: str) -> None:
        if self.initial_memory is not None:
            gc.collect()
            current_memory = psutil.Process().memory_info().rss
            memory_diff = current_memory - self.initial_memory
            if memory_diff > 10 * 1024 * 1024:
                logger.warning(
                    f"High memory usage after {operation}: {memory_diff / 1024 / 1024:.2f}MB"
                )

    def verify_button(self, button: QPushButton, enabled: bool = True) -> None:
        assert isinstance(button, QPushButton)
        assert button.isEnabled() == enabled

    def verify_label(self, label: QLabel, expected_text: str) -> None:
        assert isinstance(label, QLabel)
        assert label.text() == expected_text


@pytest.fixture
def helper():
    return DashboardTestHelper()


@pytest.fixture
def mock_controller():
    return MockController()


@pytest.fixture
def dashboard_ui(qtbot, mock_controller):
    ui = DashboardUI(mock_controller)
    mock_controller.main_ui = ui  # Set reference back to UI
    qtbot.addWidget(ui)
    ui.show()
    yield ui

    # Ensure proper cleanup
    for component in ui.ui_components[:]:
        try:
            if hasattr(component, "close"):
                component.close()
            if hasattr(component, "deleteLater"):
                component.deleteLater()
            ui.ui_components.remove(component)
        except:
            pass

    ui.close()
    qtbot.wait(100)
    gc.collect()


def test_initialization(dashboard_ui, helper):
    helper.track_memory()

    assert isinstance(dashboard_ui, QMainWindow)
    assert dashboard_ui.windowTitle() == "GynTree Dashboard"
    assert dashboard_ui.controller is not None
    assert dashboard_ui.theme_manager is not None
    assert dashboard_ui.project_ui is None
    assert dashboard_ui.result_ui is None
    assert dashboard_ui.auto_exclude_ui is None
    assert dashboard_ui.directory_tree_ui is None
    assert dashboard_ui.theme_toggle is not None
    assert dashboard_ui._welcome_label is not None

    helper.check_memory_usage("initialization")


def test_ui_components(dashboard_ui, qtbot, helper):
    helper.track_memory()

    helper.verify_label(dashboard_ui._welcome_label, "Welcome to GynTree!")
    assert dashboard_ui._welcome_label.font().weight() == QFont.Bold

    buttons = [
        dashboard_ui.projects_btn,
        dashboard_ui.manage_projects_btn,
        dashboard_ui.manage_exclusions_btn,
        dashboard_ui.analyze_directory_btn,
        dashboard_ui.view_directory_tree_btn,
    ]

    for button in buttons:
        helper.verify_button(
            button,
            enabled=button
            in [dashboard_ui.projects_btn, dashboard_ui.manage_projects_btn],
        )

    assert isinstance(dashboard_ui.theme_toggle, AnimatedToggle)

    helper.check_memory_usage("UI components")


def test_button_states(dashboard_ui, helper):
    helper.track_memory()

    assert dashboard_ui.projects_btn.isEnabled()
    assert dashboard_ui.manage_projects_btn.isEnabled()
    assert not dashboard_ui.manage_exclusions_btn.isEnabled()
    assert not dashboard_ui.analyze_directory_btn.isEnabled()
    assert not dashboard_ui.view_directory_tree_btn.isEnabled()

    dashboard_ui.enable_project_actions()

    assert dashboard_ui.manage_exclusions_btn.isEnabled()
    assert dashboard_ui.analyze_directory_btn.isEnabled()
    assert dashboard_ui.view_directory_tree_btn.isEnabled()

    helper.check_memory_usage("button states")


def test_theme_toggle(dashboard_ui, qtbot, helper):
    helper.track_memory()

    initial_theme = dashboard_ui.theme_manager.get_current_theme()
    dashboard_ui.theme_toggle.setChecked(not dashboard_ui.theme_toggle.isChecked())
    qtbot.wait(100)

    current_theme = dashboard_ui.theme_manager.get_current_theme()
    assert current_theme != initial_theme
    assert dashboard_ui.theme_toggle.isChecked() == (current_theme == "dark")

    helper.check_memory_usage("theme toggle")


def test_project_creation(dashboard_ui, qtbot, helper):
    helper.track_memory()

    project = type("Project", (), helper.default_project)()
    dashboard_ui.controller.project_controller.is_project_loaded = False
    dashboard_ui.on_project_created(project)
    qtbot.wait(100)

    assert dashboard_ui.windowTitle() == f"GynTree - {project.name}"
    assert dashboard_ui.manage_exclusions_btn.isEnabled()
    assert dashboard_ui.analyze_directory_btn.isEnabled()
    assert dashboard_ui.view_directory_tree_btn.isEnabled()
    assert dashboard_ui.controller.project_controller.is_project_loaded

    helper.check_memory_usage("project creation")


def test_project_info_update(dashboard_ui, helper):
    helper.track_memory()

    project = type(
        "Project",
        (),
        {
            "name": helper.default_project["name"],
            "start_directory": helper.default_project["start_directory"],
            "status": helper.default_project["status"],
        },
    )()

    dashboard_ui.update_project_info(project)

    assert dashboard_ui.windowTitle() == f"GynTree - {project.name}"
    expected_status = f"Current project: {project.name}, Start directory: {project.start_directory} - {project.status}"
    assert dashboard_ui.status_bar.currentMessage() == expected_status

    helper.check_memory_usage("info update")


def test_project_loading(dashboard_ui, qtbot, helper):
    helper.track_memory()

    project = type("Project", (), helper.default_project)()
    dashboard_ui.controller.project_controller.is_project_loaded = False
    # Call controller method instead of UI method directly to ensure proper state updates
    dashboard_ui.controller.on_project_loaded(project)
    qtbot.wait(100)

    assert dashboard_ui.windowTitle() == f"GynTree - {project.name}"
    assert dashboard_ui.manage_exclusions_btn.isEnabled()
    assert dashboard_ui.analyze_directory_btn.isEnabled()
    assert dashboard_ui.view_directory_tree_btn.isEnabled()
    assert dashboard_ui.controller.project_controller.is_project_loaded

    helper.check_memory_usage("project loading")


def test_auto_exclude_ui(dashboard_ui, qtbot, helper):
    helper.track_memory()

    # Set up project context first
    project = type("Project", (), helper.default_project)()
    dashboard_ui.controller.on_project_created(project)
    qtbot.wait(100)

    result = dashboard_ui.show_auto_exclude_ui(
        dashboard_ui.controller.project_context.auto_exclude_manager,
        dashboard_ui.controller.project_context.settings_manager,
        [],
        dashboard_ui.controller.project_context,
    )

    assert result is not None
    helper.check_memory_usage("auto-exclude UI")


def test_result_ui(dashboard_ui, qtbot, helper):
    helper.track_memory()

    # Set up project context first
    project = type("Project", (), helper.default_project)()
    dashboard_ui.controller.on_project_created(project)
    qtbot.wait(100)

    result = dashboard_ui.show_result(
        dashboard_ui.controller.project_context.directory_analyzer
    )

    assert result is not None
    helper.check_memory_usage("result UI")


def test_directory_tree_ui(dashboard_ui, qtbot, helper):
    helper.track_memory()

    # Set up project context first
    project = type("Project", (), helper.default_project)()
    dashboard_ui.controller.on_project_created(project)
    qtbot.wait(100)

    result = dashboard_ui.view_directory_tree_ui(
        dashboard_ui.controller.project_context.directory_analyzer.get_directory_tree()
    )

    assert result is not None
    helper.check_memory_usage("directory tree UI")


def test_exclusions_manager(dashboard_ui, qtbot, helper):
    helper.track_memory()

    # Set up project context first
    project = type("Project", (), helper.default_project)()
    dashboard_ui.controller.on_project_created(project)
    qtbot.wait(100)

    result = dashboard_ui.manage_exclusions(
        dashboard_ui.controller.project_context.settings_manager
    )

    assert result is not None
    helper.check_memory_usage("exclusions manager")


def test_error_handling(dashboard_ui, helper, mocker):
    helper.track_memory()

    mock_message_box = mocker.patch("PyQt5.QtWidgets.QMessageBox.critical")
    dashboard_ui.show_error_message("Test Error", "Test Message")
    mock_message_box.assert_called_once_with(dashboard_ui, "Test Error", "Test Message")

    helper.check_memory_usage("error handling")


def test_theme_persistence(dashboard_ui, qtbot, helper):
    helper.track_memory()

    initial_theme = dashboard_ui.theme_manager.get_current_theme()
    dashboard_ui.theme_toggle.setChecked(not dashboard_ui.theme_toggle.isChecked())
    qtbot.wait(100)

    new_dashboard = DashboardUI(dashboard_ui.controller)
    current_theme = new_dashboard.theme_manager.get_current_theme()
    assert current_theme != initial_theme
    assert new_dashboard.theme_toggle.isChecked() == (current_theme == "dark")

    new_dashboard.close()
    helper.check_memory_usage("theme persistence")


def test_window_geometry(dashboard_ui, helper):
    helper.track_memory()

    geometry = dashboard_ui.geometry()
    assert geometry.width() == 800
    assert geometry.height() == 600
    assert geometry.x() == 300
    assert geometry.y() == 300

    helper.check_memory_usage("window geometry")


def test_state_transitions(dashboard_ui, qtbot, helper):
    helper.track_memory()

    # Initial state
    states = []

    def record_state():
        return {
            "has_project": dashboard_ui.controller.project_context is not None,
            "project_loaded": dashboard_ui.controller.project_controller.is_project_loaded,
            "buttons_enabled": {
                "projects": dashboard_ui.projects_btn.isEnabled(),
                "manage": dashboard_ui.manage_projects_btn.isEnabled(),
                "exclusions": dashboard_ui.manage_exclusions_btn.isEnabled(),
                "analyze": dashboard_ui.analyze_directory_btn.isEnabled(),
                "tree": dashboard_ui.view_directory_tree_btn.isEnabled(),
            },
            "theme": dashboard_ui.theme_manager.get_current_theme(),
            "window_title": dashboard_ui.windowTitle(),
        }

    # Record initial state
    states.append(record_state())

    # Create and load project
    project = type("Project", (), helper.default_project)()
    dashboard_ui.controller.on_project_created(project)
    qtbot.wait(100)
    states.append(record_state())

    # Toggle theme
    dashboard_ui.theme_toggle.setChecked(not dashboard_ui.theme_toggle.isChecked())
    qtbot.wait(100)
    states.append(record_state())

    # Verify state transitions
    assert not states[0]["has_project"], "Should start without project"
    assert not states[0]["project_loaded"], "Should start without loaded project"
    assert states[0]["buttons_enabled"][
        "projects"
    ], "Projects button should be enabled initially"
    assert not states[0]["buttons_enabled"][
        "exclusions"
    ], "Exclusions button should be disabled initially"

    assert states[1]["has_project"], "Should have project after creation"
    assert states[1]["project_loaded"], "Project should be loaded after creation"
    assert states[1]["buttons_enabled"][
        "exclusions"
    ], "Exclusions button should be enabled after project creation"
    assert (
        states[1]["window_title"] == f"GynTree - {project.name}"
    ), "Window title should reflect project name"

    assert states[2]["theme"] != states[1]["theme"], "Theme should change after toggle"

    helper.check_memory_usage("state transitions")


def test_thread_safety(dashboard_ui, qtbot, helper):
    helper.track_memory()

    # Test concurrent operations
    project = type("Project", (), helper.default_project)()

    # Simulate rapid UI operations
    dashboard_ui.controller.on_project_created(project)
    dashboard_ui.theme_toggle.setChecked(not dashboard_ui.theme_toggle.isChecked())
    dashboard_ui.clear_directory_tree()
    dashboard_ui.update_project_info(project)
    qtbot.wait(100)

    assert dashboard_ui.controller.project_controller.is_project_loaded
    assert dashboard_ui.windowTitle() == f"GynTree - {project.name}"

    helper.check_memory_usage("thread safety")


def test_error_recovery(dashboard_ui, qtbot, helper, mocker):
    helper.track_memory()

    project = type("Project", (), helper.default_project)()
    dashboard_ui.controller.project_controller.is_project_loaded = False

    # Setup initial error mock
    def create_project_error(*args):
        dashboard_ui.controller.project_controller.is_project_loaded = False
        raise Exception("Test error")

    mock_create = mocker.patch.object(
        dashboard_ui.controller.project_controller,
        "create_project",
        side_effect=create_project_error,
    )
    mock_message_box = mocker.patch("PyQt5.QtWidgets.QMessageBox.critical")

    # First attempt - should fail
    try:
        dashboard_ui.controller.on_project_created(project)
    except Exception:
        pass

    qtbot.wait(100)

    # Verify failure state
    assert mock_message_box.called
    assert not dashboard_ui.controller.project_controller.is_project_loaded
    assert not dashboard_ui.manage_exclusions_btn.isEnabled()

    # Setup recovery mock
    def create_project_success(*args):
        dashboard_ui.controller.project_controller.is_project_loaded = True
        dashboard_ui.controller.project_controller.project_context = (
            MockProjectContext()
        )
        dashboard_ui.controller.project_controller.current_project = args[0]
        return True

    mock_create.side_effect = create_project_success
    mock_create.reset_mock()
    mock_message_box.reset_mock()

    # Second attempt - should succeed
    dashboard_ui.controller.on_project_created(project)
    qtbot.wait(100)

    # Verify recovery state
    assert mock_create.called
    assert dashboard_ui.manage_exclusions_btn.isEnabled()
    assert dashboard_ui.controller.project_controller.is_project_loaded

    helper.check_memory_usage("error recovery")


def test_ui_responsiveness(dashboard_ui, qtbot, helper):
    helper.track_memory()

    project = type("Project", (), helper.default_project)()

    # Measure response time for various operations
    start_time = time.time()

    # Project creation
    dashboard_ui.controller.on_project_created(project)
    qtbot.wait(100)

    # Theme toggle
    dashboard_ui.theme_toggle.setChecked(not dashboard_ui.theme_toggle.isChecked())
    qtbot.wait(100)

    # UI updates
    dashboard_ui.update_project_info(project)
    dashboard_ui.clear_directory_tree()
    dashboard_ui.clear_analysis()

    end_time = time.time()
    operation_time = end_time - start_time

    # Operations should complete within reasonable time
    assert (
        operation_time < 2.0
    ), f"UI operations took too long: {operation_time:.2f} seconds"

    helper.check_memory_usage("UI responsiveness")


def test_component_lifecycle(dashboard_ui, qtbot, helper):
    helper.track_memory()

    project = type("Project", (), helper.default_project)()
    dashboard_ui.controller.on_project_created(project)
    qtbot.wait(100)

    # Create various UI components
    components = []

    auto_exclude_ui = dashboard_ui.show_auto_exclude_ui(
        dashboard_ui.controller.project_context.auto_exclude_manager,
        dashboard_ui.controller.project_context.settings_manager,
        [],
        dashboard_ui.controller.project_context,
    )
    components.append(auto_exclude_ui)

    result_ui = dashboard_ui.show_result(
        dashboard_ui.controller.project_context.directory_analyzer
    )
    components.append(result_ui)

    tree_ui = dashboard_ui.view_directory_tree_ui(
        dashboard_ui.controller.project_context.directory_analyzer.get_directory_tree()
    )
    components.append(tree_ui)

    # Verify components are tracked
    for component in components:
        assert component in dashboard_ui.ui_components

    # Record initial count
    initial_component_count = len(dashboard_ui.ui_components)

    # Close and remove components
    for component in components:
        if component in dashboard_ui.ui_components:
            component.close()
            dashboard_ui.ui_components.remove(component)
            qtbot.wait(50)
            QApplication.processEvents()

    qtbot.wait(200)

    # Verify cleanup
    assert len(dashboard_ui.ui_components) < initial_component_count
    assert all(c not in dashboard_ui.ui_components for c in components)

    helper.check_memory_usage("component lifecycle")


def test_settings_persistence(dashboard_ui, qtbot, helper):
    helper.track_memory()

    # Test theme persistence
    initial_theme = dashboard_ui.theme_manager.get_current_theme()
    dashboard_ui.theme_toggle.setChecked(not dashboard_ui.theme_toggle.isChecked())
    qtbot.wait(100)

    # Create new instance to verify persistence
    new_dashboard = DashboardUI(dashboard_ui.controller)
    qtbot.addWidget(new_dashboard)

    assert new_dashboard.theme_manager.get_current_theme() != initial_theme
    assert new_dashboard.theme_toggle.isChecked() == (
        new_dashboard.theme_manager.get_current_theme() == "dark"
    )

    new_dashboard.close()
    helper.check_memory_usage("settings persistence")


def test_memory_cleanup(dashboard_ui, qtbot, helper):
    helper.track_memory()

    dashboard_ui.show_dashboard()
    qtbot.wait(100)

    dashboard_ui.clear_directory_tree()
    dashboard_ui.clear_analysis()
    dashboard_ui.clear_exclusions()

    gc.collect()
    current_memory = psutil.Process().memory_info().rss
    memory_diff = current_memory - helper.initial_memory

    assert memory_diff < 10 * 1024 * 1024

    helper.check_memory_usage("memory cleanup")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
