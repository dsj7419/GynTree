import os
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, 
                           QStatusBar, QHBoxLayout, QPushButton, QMessageBox)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from components.UI.ProjectUI import ProjectUI
from components.UI.AutoExcludeUI import AutoExcludeUI
from components.UI.ResultUI import ResultUI
from components.UI.DirectoryTreeUI import DirectoryTreeUI
from components.UI.ExclusionsManagerUI import ExclusionsManagerUI
from components.UI.ProjectManagementUI import ProjectManagementUI
from components.UI.animated_toggle import AnimatedToggle
from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager
import logging

logger = logging.getLogger(__name__)

class DashboardUI(QMainWindow):
    project_created = pyqtSignal(object)
    project_loaded = pyqtSignal(object)
    theme_changed = pyqtSignal(str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.theme_manager = ThemeManager.getInstance()
        self.project_ui = None
        self.result_ui = None
        self.auto_exclude_ui = None
        self.exclusions_ui = None
        self.directory_tree_ui = None
        self.theme_toggle = None
        self._welcome_label = None
        self.ui_components = []  # Track UI components for cleanup
        self.initUI()

    def initUI(self):
        """Initialize the UI components"""
        self.setWindowTitle('GynTree Dashboard')
        icon_path = get_resource_path('assets/images/GynTree_logo.ico')
        self.setWindowIcon(QIcon(icon_path))

        # Create central widget and main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Theme toggle setup - Put this first to ensure it's always visible
        theme_toggle_layout = QHBoxLayout()
        self.theme_toggle = AnimatedToggle(
            checked_color="#FFB000",
            pulse_checked_color="#44FFB000"
        )
        self.theme_toggle.setFixedSize(self.theme_toggle.sizeHint())
        current_theme = self.theme_manager.get_current_theme()
        self.theme_toggle.setChecked(current_theme == 'dark')
        self.theme_toggle.stateChanged.connect(self.on_theme_toggle_changed)
        self.theme_toggle.setVisible(True)
        self.theme_toggle.setEnabled(True)
        theme_toggle_layout.addStretch()
        theme_toggle_layout.addWidget(self.theme_toggle)
        main_layout.addLayout(theme_toggle_layout)

        # Logo setup
        header_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_path = get_resource_path('assets/images/gyntree_logo.png')
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logger.warning(f"Logo file not found at {logo_path}")

        # Welcome label setup
        self._welcome_label = QLabel('Welcome to GynTree!')
        self._welcome_label.setFont(QFont('Arial', 24, QFont.Bold))
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(self._welcome_label)
        header_layout.setAlignment(Qt.AlignCenter)
        main_layout.addLayout(header_layout)

        # Button setup
        self.projects_btn = self.create_styled_button('Create New/Open a Project')
        self.manage_projects_btn = self.create_styled_button('Manage Projects')
        self.manage_exclusions_btn = self.create_styled_button('Manage Exclusions')
        self.analyze_directory_btn = self.create_styled_button('Analyze Directory')
        self.view_directory_tree_btn = self.create_styled_button('View Directory Tree')

        # Initialize button states
        self.manage_exclusions_btn.setEnabled(False)
        self.analyze_directory_btn.setEnabled(False)
        self.view_directory_tree_btn.setEnabled(False)

        # Add buttons to layout
        for btn in [self.projects_btn, self.manage_projects_btn, self.manage_exclusions_btn,
                   self.analyze_directory_btn, self.view_directory_tree_btn]:
            main_layout.addWidget(btn)

        # Connect button signals
        self.projects_btn.clicked.connect(self.show_project_ui)
        self.manage_projects_btn.clicked.connect(self.controller.manage_projects)
        self.manage_exclusions_btn.clicked.connect(self.controller.manage_exclusions)
        self.analyze_directory_btn.clicked.connect(self.controller.analyze_directory)
        self.view_directory_tree_btn.clicked.connect(self.controller.view_directory_tree)

        # Status bar setup
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Set window properties
        self.setGeometry(300, 300, 800, 600)
        
        # Apply initial theme
        self.theme_manager.apply_theme(self)

    def create_styled_button(self, text):
        """Create a styled button with consistent formatting"""
        btn = QPushButton(text)
        font = QFont('Arial')
        font.setPointSize(14)
        btn.setFont(font)
        return btn

    def on_theme_toggle_changed(self, state):
        """Handle theme toggle state changes"""
        new_theme = 'dark' if state else 'light'
        self.theme_manager.set_theme(new_theme)
        self.theme_manager.apply_theme(self)
        self.theme_changed.emit(new_theme)

    def toggle_theme(self):
        """Toggle the current theme"""
        new_theme = self.theme_manager.toggle_theme()
        self.theme_toggle.setChecked(new_theme == 'dark')
        self.theme_changed.emit(new_theme)

    def show_dashboard(self):
        """Show the main dashboard window"""
        self.show()
        self.raise_()
        self.activateWindow()

    def show_project_ui(self):
        """Show the unified project UI for creating or loading projects"""
        if self.project_ui:
            self.project_ui.close()
            self.project_ui = None

        self.project_ui = ProjectUI(self.controller)
        self.project_ui.project_created.connect(self.on_project_created)
        self.project_ui.project_loaded.connect(self.on_project_loaded)
        self.ui_components.append(self.project_ui)
        self.project_ui.show()
        return self.project_ui

    def show_project_management(self):
        """Show the project management UI"""
        management_ui = ProjectManagementUI(self.controller, self.theme_manager)
        self.ui_components.append(management_ui)
        management_ui.show()
        return management_ui

    def on_project_created(self, project):
        """Handle project created event"""
        logger.info(f"Project creation signal received: {project.name}")
        self.controller.on_project_created(project)
        self.update_project_info(project)
        
    def on_project_loaded(self, project):
        """Handle project loaded event"""
        self.update_project_info(project)

    def show_auto_exclude_ui(self, auto_exclude_manager, settings_manager, formatted_recommendations, project_context):
        """Show the auto exclude UI window"""
        mock_exclude_ui = getattr(self, '_mock_auto_exclude_ui', None)
        if mock_exclude_ui:
            mock_exclude_ui.show()
            return mock_exclude_ui
        
        self.auto_exclude_ui = AutoExcludeUI(auto_exclude_manager, settings_manager, formatted_recommendations, project_context)
        self.ui_components.append(self.auto_exclude_ui)
        self.auto_exclude_ui.show()
        return self.auto_exclude_ui

    def show_result(self, directory_analyzer):
        """Show the results UI window"""
        mock_result_ui = getattr(self, '_mock_result_ui', None)
        if mock_result_ui:
            mock_result_ui.show()
            return mock_result_ui
            
        if self.controller.project_controller.project_context:
            self.result_ui = ResultUI(self.controller, self.theme_manager, directory_analyzer)
            self.ui_components.append(self.result_ui)
            self.result_ui.show()
            return self.result_ui
        return None

    def manage_exclusions(self, settings_manager):
        """Show the exclusions manager UI"""
        mock_exclusions_ui = getattr(self, '_mock_exclusions_ui', None)
        if mock_exclusions_ui:
            mock_exclusions_ui.show()
            return mock_exclusions_ui
            
        if self.controller.project_controller.project_context:
            self.exclusions_ui = ExclusionsManagerUI(self.controller, self.theme_manager, settings_manager)
            self.ui_components.append(self.exclusions_ui)
            self.exclusions_ui.show()
            return self.exclusions_ui
            
        QMessageBox.warning(self, "No Project", "Please load or create a project before managing exclusions.")
        return None

    def view_directory_tree_ui(self, result):
        """Show the directory tree UI"""
        mock_tree_ui = getattr(self, '_mock_directory_tree_ui', None)
        if mock_tree_ui:
            mock_tree_ui.update_tree(result)
            mock_tree_ui.show()
            return mock_tree_ui
            
        if not self.directory_tree_ui:
            self.directory_tree_ui = DirectoryTreeUI(self.controller, self.theme_manager)
        self.directory_tree_ui.update_tree(result)
        self.ui_components.append(self.directory_tree_ui)
        self.directory_tree_ui.show()
        return self.directory_tree_ui

    def update_project_info(self, project):
        """Update the UI with current project information"""
        self.setWindowTitle(f"GynTree - {project.name}")
        status_msg = f"Current project: {project.name}, Start directory: {project.start_directory}"
        if hasattr(project, 'status'):
            status_msg = f"{status_msg} - {project.status}"
        self.status_bar.showMessage(status_msg)
        self.enable_project_actions()

    def enable_project_actions(self):
        """Enable project-related buttons"""
        self.manage_exclusions_btn.setEnabled(True)
        self.analyze_directory_btn.setEnabled(True)
        self.view_directory_tree_btn.setEnabled(True)

    def clear_directory_tree(self):
        """Clear the directory tree view"""
        if hasattr(self, 'directory_tree_view'):
            self.directory_tree_view.clear()
        logger.debug("Directory tree cleared")

    def clear_analysis(self):
        """Clear the analysis results"""
        if hasattr(self, 'analysis_result_view'):
            self.analysis_result_view.clear()
        logger.debug("Analysis results cleared")

    def clear_exclusions(self):
        """Clear the exclusions list"""
        if hasattr(self, 'exclusions_list_view'):
            self.exclusions_list_view.clear()
        logger.debug("Exclusions list cleared")

    def show_error_message(self, title, message):
        """Show an error message dialog"""
        QMessageBox.critical(self, title, message)

    def closeEvent(self, event):
        """Handle window close event and cleanup"""
        for component in self.ui_components:
            try:
                if component and hasattr(component, 'close'):
                    component.close()
            except Exception as e:
                logger.debug(f"Non-critical UI component cleanup warning: {e}")
        super().closeEvent(event)