import gc
import logging
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
        self.project_controller = type(
            "ProjectController", (), {"project_context": None}
        )()
        self.theme_manager = ThemeManager.getInstance()
        self.manage_projects = lambda: None
        self.manage_exclusions = lambda: None
        self.analyze_directory = lambda: None
        self.view_directory_tree = lambda: None
        self.on_project_created = lambda project: None

    def show_project_ui(self):
        pass


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
    qtbot.addWidget(ui)
    ui.show()
    yield ui
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


def test_project_creation(dashboard_ui, qtbot, helper, mocker):
    helper.track_memory()

    mock_project_ui = mocker.Mock(spec=ProjectUI)
    mock_project_ui.show = mocker.Mock()
    mocker.patch("components.UI.ProjectUI.ProjectUI", return_value=mock_project_ui)

    project = type("Project", (), helper.default_project)()
    dashboard_ui.on_project_created(project)
    qtbot.wait(100)

    assert dashboard_ui.windowTitle() == f"GynTree - {project.name}"
    assert dashboard_ui.manage_exclusions_btn.isEnabled()
    assert dashboard_ui.analyze_directory_btn.isEnabled()
    assert dashboard_ui.view_directory_tree_btn.isEnabled()

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
    dashboard_ui.on_project_loaded(project)
    qtbot.wait(100)

    assert dashboard_ui.windowTitle() == f"GynTree - {project.name}"
    assert dashboard_ui.manage_exclusions_btn.isEnabled()
    assert dashboard_ui.analyze_directory_btn.isEnabled()
    assert dashboard_ui.view_directory_tree_btn.isEnabled()

    helper.check_memory_usage("project loading")


def test_auto_exclude_ui(dashboard_ui, qtbot, helper, mocker):
    helper.track_memory()

    mock_auto_exclude_ui = mocker.Mock(spec=AutoExcludeUI)
    mock_auto_exclude_ui.show = mocker.Mock()
    dashboard_ui._mock_auto_exclude_ui = mock_auto_exclude_ui

    mock_manager = mocker.Mock()
    mock_settings = mocker.Mock()

    result = dashboard_ui.show_auto_exclude_ui(
        mock_manager, mock_settings, [], mocker.Mock()
    )

    assert result == mock_auto_exclude_ui
    assert mock_auto_exclude_ui.show.called

    helper.check_memory_usage("auto-exclude UI")


def test_result_ui(dashboard_ui, qtbot, helper, mocker):
    helper.track_memory()

    mock_result_ui = mocker.Mock(spec=ResultUI)
    mock_result_ui.show = mocker.Mock()
    dashboard_ui._mock_result_ui = mock_result_ui

    dashboard_ui.controller.project_controller.project_context = mocker.Mock()
    result = dashboard_ui.show_result(mocker.Mock())

    assert result == mock_result_ui
    assert mock_result_ui.show.called

    helper.check_memory_usage("result UI")


def test_directory_tree_ui(dashboard_ui, qtbot, helper, mocker):
    helper.track_memory()

    mock_tree_ui = mocker.Mock(spec=DirectoryTreeUI)
    mock_tree_ui.show = mocker.Mock()
    mock_tree_ui.update_tree = mocker.Mock()
    dashboard_ui._mock_directory_tree_ui = mock_tree_ui

    result = dashboard_ui.view_directory_tree_ui({})

    assert result == mock_tree_ui
    assert mock_tree_ui.update_tree.called
    assert mock_tree_ui.show.called

    helper.check_memory_usage("directory tree UI")


def test_exclusions_manager(dashboard_ui, qtbot, helper, mocker):
    helper.track_memory()

    mock_exclusions_ui = mocker.Mock(spec=ExclusionsManagerUI)
    mock_exclusions_ui.show = mocker.Mock()
    dashboard_ui._mock_exclusions_ui = mock_exclusions_ui

    dashboard_ui.controller.project_controller.project_context = mocker.Mock()
    mock_settings = mocker.Mock()

    result = dashboard_ui.manage_exclusions(mock_settings)

    assert result == mock_exclusions_ui
    assert mock_exclusions_ui.show.called

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
