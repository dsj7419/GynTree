# tests/unit/test_ui_state.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton, QWidget
from PyQt5.QtCore import QSize, Qt, QTimer, QThread
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QCloseEvent

from components.UI.DashboardUI import DashboardUI
from components.UI.ProjectUI import ProjectUI
from components.UI.AutoExcludeUI import AutoExcludeUI
from components.UI.ExclusionsManagerUI import ExclusionsManagerUI
from utilities.theme_manager import ThemeManager

@pytest.fixture(scope='function')
def app(qapp):
    """Provides clean QApplication instance per test"""
    yield qapp
    QTest.qWait(10)  # Allow pending events to process
    
@pytest.fixture(scope='function')
def mock_controller():
    """Provides mock controller with required setup"""
    controller = Mock()
    controller.project_controller = Mock()
    controller.project_controller.project_context = Mock()
    controller.project_controller.project_manager = Mock()
    controller.project_controller.project_manager.list_projects = Mock(return_value=[])
    return controller

@pytest.fixture(scope='function')
def theme_manager():
    """Provides isolated theme manager instance"""
    manager = ThemeManager.getInstance()
    manager.apply_theme = Mock()
    original_theme = manager.get_current_theme()
    yield manager
    manager.set_theme(original_theme)
    QTest.qWait(10)

class TestUIState:
    def cleanup_message_boxes(self):
        """Helper method to clean up any lingering message boxes"""
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMessageBox):
                widget.close()
                widget.deleteLater()
        QTest.qWait(10)

    @pytest.fixture(autouse=True)
    def setup_cleanup(self, request):
        """Automatic cleanup after each test"""
        widgets = []
        def cleanup():
            QTest.qWait(10)
            self.cleanup_message_boxes()  # Add message box cleanup
            for widget in widgets:
                if widget.isVisible():
                    widget.close()
                widget.deleteLater()
            QTest.qWait(50)
            self.cleanup_message_boxes()  # One final check for message boxes
        request.addfinalizer(cleanup)
        self.widgets = widgets
        
    def register_widget(self, widget):
        """Register widget for cleanup"""
        self.widgets.append(widget)
        return widget

    def test_dashboard_initial_state(self, app, mock_controller):
        ui = self.register_widget(DashboardUI(mock_controller))
        
        assert not ui.manage_exclusions_btn.isEnabled()
        assert not ui.analyze_directory_btn.isEnabled()
        assert not ui.view_directory_tree_btn.isEnabled()
        assert ui.theme_toggle is not None
        assert ui.theme_toggle.isEnabled()

    def test_dashboard_project_loaded_state(self, app, mock_controller):
        ui = self.register_widget(DashboardUI(mock_controller))
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.start_directory = "/test/path"
        
        with patch.object(QMessageBox, 'information', return_value=QMessageBox.Ok):
            ui.on_project_loaded(mock_project)
            QTest.qWait(10)
        
        assert ui.manage_exclusions_btn.isEnabled()
        assert ui.analyze_directory_btn.isEnabled()
        assert ui.view_directory_tree_btn.isEnabled()
        assert "Test Project" in ui.windowTitle()

    def test_theme_state_persistence(self, app, mock_controller, theme_manager):
        ui = self.register_widget(DashboardUI(mock_controller))
        initial_theme = 'light'
        ui.theme_manager.current_theme = initial_theme
        
        with patch.object(theme_manager, 'apply_theme'):
            ui.toggle_theme()
            QTest.qWait(10)
            new_theme = ui.theme_manager.get_current_theme()
            
            assert initial_theme != new_theme
            assert ui.theme_toggle.isChecked() == (new_theme == 'dark')

    def test_error_state_handling(self, app, mock_controller):
        ui = self.register_widget(DashboardUI(mock_controller))
        
        with patch.object(QMessageBox, 'critical', return_value=QMessageBox.Ok) as mock_critical:
            ui.show_error_message("Test Error", "Error Message")
            QTest.qWait(10)
            mock_critical.assert_called_once()
            
        assert ui.isEnabled()

    def test_ui_component_cleanup(self, app, mock_controller):
        ui = self.register_widget(DashboardUI(mock_controller))
        mock_components = [Mock() for _ in range(3)]
        for component in mock_components:
            component.close = Mock()
            ui.ui_components.append(component)
        
        event = QCloseEvent()
        ui.closeEvent(event)
        QTest.qWait(10)
        
        for component in mock_components:
            component.close.assert_called_once()

    def test_auto_exclude_ui_state(self, app, mock_controller):
        # Setup mock manager with proper return values
        mock_manager = Mock()
        mock_manager.get_recommendations.return_value = {
            'root_exclusions': set(),
            'excluded_dirs': set(),
            'excluded_files': set()
        }
        
        mock_settings = Mock()
        mock_context = Mock()
        mock_context.settings_manager = Mock()
        mock_context.settings_manager.get_root_exclusions = Mock(return_value=[])
        mock_context.settings_manager.get_excluded_dirs = Mock(return_value=[])
        mock_context.settings_manager.get_excluded_files = Mock(return_value=[])
        
        # Patch QMessageBox to prevent popups during test
        with patch('PyQt5.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok), \
            patch('PyQt5.QtWidgets.QMessageBox.warning', return_value=QMessageBox.Ok):
            
            ui = self.register_widget(AutoExcludeUI(
                mock_manager, mock_settings, [], mock_context,
                theme_manager=ThemeManager.getInstance()
            ))
            
            # Process any pending events
            QTest.qWait(50)
            
            assert ui.tree_widget is not None
            assert ui.tree_widget.columnCount() == 2
            
            buttons = ui.findChildren(QPushButton)
            assert all(button.isEnabled() for button in buttons)
            
            # Close any open dialogs
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMessageBox):
                    widget.close()
            
            # Final cleanup
            ui.close()
            QTest.qWait(50)

    def test_exclusions_manager_state(self, app, mock_controller):
        # Close any existing message boxes before starting
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMessageBox):
                widget.close()
                widget.deleteLater()
        QTest.qWait(10)
        
        mock_theme_manager = Mock()
        mock_settings = Mock()
        mock_theme_manager.apply_theme = Mock()
        mock_settings.get_root_exclusions = Mock(return_value=[])
        mock_settings.get_all_exclusions = Mock(return_value={
            'excluded_dirs': [],
            'excluded_files': []
        })
        
        with patch('PyQt5.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok), \
            patch('PyQt5.QtWidgets.QMessageBox.warning', return_value=QMessageBox.Ok):
            
            ui = self.register_widget(ExclusionsManagerUI(mock_controller, mock_theme_manager, mock_settings))
            ui._skip_show_event = True
            
            assert ui.exclusion_tree is not None
            assert ui.root_tree is not None
            
            ui.remove_selected()
            QTest.qWait(10)
            assert ui.isEnabled()
            
            # Final cleanup
            ui.close()
            QTest.qWait(50)
            
            # Cleanup any remaining dialogs
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMessageBox):
                    widget.close()
                    widget.deleteLater()
            QTest.qWait(10)

    def test_window_geometry_persistence(self, app, mock_controller):
        ui = self.register_widget(DashboardUI(mock_controller))
        initial_geometry = ui.geometry()
        
        new_size = QSize(
            initial_geometry.size().width() + 100,
            initial_geometry.size().height() + 100
        )
        ui.resize(new_size)
        QTest.qWait(10)
        
        assert ui.size() == new_size

    def test_ui_responsiveness(self, app, mock_controller):
        ui = self.register_widget(DashboardUI(mock_controller))
        
        # Close any existing message boxes before starting
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMessageBox):
                widget.close()
                widget.deleteLater()
        QTest.qWait(10)
        
        with patch.object(ui, 'update_project_info') as mock_update, \
            patch('PyQt5.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok), \
            patch('PyQt5.QtWidgets.QMessageBox.warning', return_value=QMessageBox.Ok):
            
            for _ in range(100):
                mock_project = Mock()
                ui.update_project_info(mock_project)
                QTest.qWait(1)
            
            # Ensure all events are processed
            QTest.qWait(50)
            
            assert ui.isEnabled()
            assert mock_update.call_count == 100
            
            # Final cleanup of any remaining dialogs
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMessageBox):
                    widget.close()
                    widget.deleteLater()
            QTest.qWait(10)

    def test_theme_application_to_components(self, app, mock_controller):
        ui = self.register_widget(DashboardUI(mock_controller))
        initial_stylesheet = 'QWidget{}'
        ui.setStyleSheet(initial_stylesheet)
        
        with patch.object(ThemeManager, 'apply_theme') as mock_apply_theme:
            ui.toggle_theme()
            QTest.qWait(10)
            assert mock_apply_theme.called

    def test_concurrent_ui_updates(self, app, mock_controller):
        ui = self.register_widget(DashboardUI(mock_controller))
        
        # Close any existing message boxes before starting
        self.cleanup_message_boxes()
        
        def delayed_update():
            for _ in range(5):
                mock_project = Mock()
                mock_project.name = f"Project_{_}"
                ui.update_project_info(mock_project)
                QTest.qWait(10)
        
        with patch.object(ui, 'update_project_info', wraps=ui.update_project_info), \
            patch('PyQt5.QtWidgets.QMessageBox.information', return_value=QMessageBox.Ok), \
            patch('PyQt5.QtWidgets.QMessageBox.warning', return_value=QMessageBox.Ok):
            
            QTimer.singleShot(0, delayed_update)
            QTest.qWait(100)
            
            assert ui.isEnabled()
            assert ui.status_bar.currentMessage() is not None
            
            # Final cleanup
            ui.close()
            QTest.qWait(50)
            self.cleanup_message_boxes()