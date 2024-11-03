import os
import time

import pytest

# Import conftest utilities
from conftest import QT_WAIT_TIMEOUT, logger_context, mock_msg_box, test_artifacts
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QMessageBox

from components.UI.DashboardUI import DashboardUI
from controllers.AppController import AppController


def wait_for_condition(qtbot, condition, timeout=2000, interval=50):
    """Helper function to wait for a condition with debug"""
    end_time = time.time() + (timeout / 1000.0)
    while time.time() < end_time:
        QApplication.processEvents()
        if condition():
            return True
        QTest.qWait(interval)
    return False


class TestSystemIntegration:
    @pytest.fixture(autouse=True)
    def setup_test_dir(self, tmp_path):
        """Create test directory structure"""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir(parents=True)
        yield project_dir

    @pytest.mark.cleanup
    def test_end_to_end_project_workflow(
        self, qapp, mock_project, qtbot, setup_test_dir, monkeypatch
    ):
        monkeypatch.setattr(QMessageBox, "warning", mock_msg_box)
        monkeypatch.setattr(QMessageBox, "critical", mock_msg_box)

        mock_project.start_directory = str(setup_test_dir)
        controller = AppController()
        test_artifacts.track_widget(controller.main_ui)

        controller.on_project_created(mock_project)
        QTest.qWait(QT_WAIT_TIMEOUT)

        assert controller.project_context is not None
        assert controller.project_context.is_initialized
        assert controller.main_ui.manage_exclusions_btn.isEnabled()
        assert "test_project" in controller.main_ui.windowTitle()

        controller.analyze_directory()
        QTest.qWait(500)
        assert controller.project_context.directory_analyzer is not None

        QApplication.processEvents()
        controller.cleanup()

    @pytest.mark.cleanup
    def test_thread_controller_integration(
        self, qapp, mock_project, qtbot, setup_test_dir, monkeypatch
    ):
        monkeypatch.setattr(QMessageBox, "warning", mock_msg_box)
        monkeypatch.setattr(QMessageBox, "critical", mock_msg_box)

        mock_project.start_directory = str(setup_test_dir)
        controller = AppController()
        test_artifacts.track_widget(controller.main_ui)

        controller.on_project_created(mock_project)
        QTest.qWait(QT_WAIT_TIMEOUT)

        initial_workers = len(controller.thread_controller.active_workers)

        controller.analyze_directory()
        controller.view_directory_tree()

        def check_workers():
            current = len(controller.thread_controller.active_workers)
            return current >= initial_workers

        assert wait_for_condition(qtbot, check_workers)
        QApplication.processEvents()
        controller.cleanup()

    @pytest.mark.cleanup
    def test_resource_cleanup_integration(
        self, qapp, mock_project, qtbot, setup_test_dir, monkeypatch
    ):
        monkeypatch.setattr(QMessageBox, "warning", mock_msg_box)
        monkeypatch.setattr(QMessageBox, "critical", mock_msg_box)

        mock_project.start_directory = str(setup_test_dir)
        controller = AppController()
        test_artifacts.track_widget(controller.main_ui)

        controller.on_project_created(mock_project)
        QTest.qWait(QT_WAIT_TIMEOUT)

        controller.view_directory_tree()
        controller.manage_exclusions()

        initial_components = len(controller.ui_components)
        for component in controller.ui_components:
            test_artifacts.track_widget(component)

        QApplication.processEvents()
        controller.cleanup()
        QTest.qWait(200)

        assert len(controller.ui_components) < initial_components
        assert not controller.thread_controller.active_workers

    @pytest.mark.cleanup
    def test_project_type_detection_integration(
        self, qapp, mock_project, setup_test_dir, monkeypatch
    ):
        monkeypatch.setattr(QMessageBox, "warning", mock_msg_box)
        monkeypatch.setattr(QMessageBox, "critical", mock_msg_box)

        project_dir = setup_test_dir

        (project_dir / "setup.py").write_text("# Python setup file")
        (project_dir / "package.json").write_text('{"name": "test"}')

        project = mock_project.__class__(
            name="multi_project", start_directory=str(project_dir)
        )

        controller = AppController()
        test_artifacts.track_widget(controller.main_ui)

        controller.on_project_created(project)
        QTest.qWait(QT_WAIT_TIMEOUT)

        assert len(controller.project_context.project_types) > 0
        assert controller.project_context.detected_types is not None
        assert "python" in controller.project_context.project_types
        assert "javascript" in controller.project_context.project_types

        QApplication.processEvents()
        controller.cleanup()

    @pytest.mark.cleanup
    def test_error_handling_integration(
        self, qapp, mock_project, setup_test_dir, monkeypatch
    ):
        monkeypatch.setattr(QMessageBox, "warning", mock_msg_box)
        monkeypatch.setattr(QMessageBox, "critical", mock_msg_box)

        nonexistent_path = str(setup_test_dir / "nonexistent")
        valid_path = str(setup_test_dir / "valid")
        os.makedirs(valid_path)

        controller = AppController()
        test_artifacts.track_widget(controller.main_ui)

        mock_project.start_directory = nonexistent_path
        controller.on_project_created(mock_project)
        assert controller.project_context is None

        mock_project.start_directory = valid_path
        controller.on_project_created(mock_project)
        QTest.qWait(QT_WAIT_TIMEOUT)
        assert controller.project_context is not None

        QApplication.processEvents()
        controller.cleanup()

    @pytest.mark.cleanup
    def test_auto_exclude_integration(
        self, qapp, mock_project, qtbot, setup_test_dir, monkeypatch
    ):
        monkeypatch.setattr(QMessageBox, "warning", mock_msg_box)
        monkeypatch.setattr(QMessageBox, "critical", mock_msg_box)

        mock_project.start_directory = str(setup_test_dir)
        controller = AppController()
        test_artifacts.track_widget(controller.main_ui)

        with logger_context() as test_logger:
            controller.on_project_created(mock_project)

            def check_auto_exclude():
                return (
                    controller.project_context
                    and controller.project_context.auto_exclude_manager
                    and controller.project_context.auto_exclude_manager.get_recommendations()
                )

            assert wait_for_condition(qtbot, check_auto_exclude)

            recommendations = (
                controller.project_context.auto_exclude_manager.get_recommendations()
            )
            assert isinstance(recommendations, dict)

            QApplication.processEvents()
            controller.cleanup()

    @pytest.mark.cleanup
    def test_settings_integration(
        self, qapp, mock_project, qtbot, setup_test_dir, monkeypatch
    ):
        monkeypatch.setattr(QMessageBox, "warning", mock_msg_box)
        monkeypatch.setattr(QMessageBox, "critical", mock_msg_box)

        mock_project.start_directory = str(setup_test_dir)
        controller = AppController()
        test_artifacts.track_widget(controller.main_ui)

        # Show the main window and wait
        controller.main_ui.show()
        qtbot.waitForWindowShown(controller.main_ui)
        QTest.qWait(500)  # Give window time to settle

        # Create project and wait for initialization
        controller.on_project_created(mock_project)
        QTest.qWait(QT_WAIT_TIMEOUT)

        # Ensure project context is initialized
        def project_ready():
            return (
                controller.project_context is not None
                and controller.project_context.is_initialized
                and controller.main_ui.isVisible()
            )

        assert wait_for_condition(qtbot, project_ready, timeout=2000)

        original_theme = controller.theme_manager.get_current_theme()
        print(f"\nOriginal theme: {original_theme}")

        # Connect signals before toggle
        theme_changed = False
        toggle_changed = False
        new_theme = None

        def on_theme_changed(theme):
            nonlocal theme_changed, new_theme
            theme_changed = True
            new_theme = theme
            print(f"Theme changed signal received: {theme}")

        def on_toggle_changed(state):
            nonlocal toggle_changed
            toggle_changed = True
            print(f"Toggle state changed: {state}")

        controller.theme_manager.themeChanged.connect(on_theme_changed)
        controller.main_ui.theme_toggle.stateChanged.connect(on_toggle_changed)

        # Verify toggle exists and is accessible
        assert controller.main_ui.theme_toggle is not None, "Theme toggle not created"
        assert controller.main_ui.theme_toggle.isVisible(), "Theme toggle not visible"
        print(f"Initial toggle state: {controller.main_ui.theme_toggle.isChecked()}")

        # Click the toggle with mouse
        toggle_center = controller.main_ui.theme_toggle.rect().center()
        qtbot.mouseClick(
            controller.main_ui.theme_toggle, Qt.LeftButton, pos=toggle_center
        )

        QTest.qWait(500)
        QApplication.processEvents()

        print(
            f"Toggle state after click: {controller.main_ui.theme_toggle.isChecked()}"
        )
        print(f"Current theme: {controller.theme_manager.get_current_theme()}")

        # Final state check
        final_theme = controller.theme_manager.get_current_theme()
        final_toggle_state = controller.main_ui.theme_toggle.isChecked()

        print(f"Final state - Theme: {final_theme}, Toggle: {final_toggle_state}")

        # Cleanup
        QApplication.processEvents()
        controller.cleanup()

        # Assertions
        assert theme_changed, "Theme changed signal not received"
        assert toggle_changed, "Toggle state changed signal not received"
        assert final_theme != original_theme, "Theme did not change"
        assert final_toggle_state == (
            final_theme == "dark"
        ), "Toggle state doesn't match theme"
