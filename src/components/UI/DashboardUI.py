import os
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, 
                             QStatusBar, QHBoxLayout, QPushButton, QMessageBox)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt
from components.UI.ProjectUI import ProjectUI
from components.UI.AutoExcludeUI import AutoExcludeUI
from components.UI.ResultUI import ResultUI
from components.UI.DirectoryTreeUI import DirectoryTreeUI
from components.UI.ExclusionsManagerUI import ExclusionsManagerUI
from components.UI.animated_toggle import AnimatedToggle
from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager
import logging

logger = logging.getLogger(__name__)

class DashboardUI(QMainWindow):
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
        self.initUI()

        # Connect controller signals
        self.controller.project_created.connect(self.on_project_created)
        self.controller.project_loaded.connect(self.on_project_loaded)

    def initUI(self):
        self.setWindowTitle('GynTree Dashboard')
        self.setWindowIcon(QIcon(get_resource_path('assets/images/GynTree_logo.ico')))

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        logo_label = QLabel()
        logo_path = get_resource_path('assets/images/gyntree_logo.png')
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logger.warning(f"Logo file not found at {logo_path}")

        welcome_label = QLabel('Welcome to GynTree!')
        welcome_label.setFont(QFont('Arial', 24, QFont.Bold))

        header_layout = QHBoxLayout()
        header_layout.addWidget(logo_label)
        header_layout.addWidget(welcome_label)
        header_layout.setAlignment(Qt.AlignCenter)
        main_layout.addLayout(header_layout)

        # Animated light/dark theme toggle
        theme_toggle_layout = QHBoxLayout()
        self.theme_toggle = AnimatedToggle(
            checked_color="#FFB000",
            pulse_checked_color="#44FFB000"
        )
        self.theme_toggle.setFixedSize(self.theme_toggle.sizeHint())
        self.theme_toggle.setChecked(self.theme_manager.get_current_theme() == 'dark')
        self.theme_toggle.stateChanged.connect(self.toggle_theme)
        theme_toggle_layout.addWidget(self.theme_toggle)
        theme_toggle_layout.setAlignment(Qt.AlignRight)
        main_layout.addLayout(theme_toggle_layout)

        self.create_project_btn = self.create_styled_button('Create Project')
        self.load_project_btn = self.create_styled_button('Load Project')
        self.manage_exclusions_btn = self.create_styled_button('Manage Exclusions')
        self.analyze_directory_btn = self.create_styled_button('Analyze Directory')
        self.view_directory_tree_btn = self.create_styled_button('View Directory Tree')

        for btn in [self.create_project_btn, self.load_project_btn, self.manage_exclusions_btn,
                    self.analyze_directory_btn, self.view_directory_tree_btn]:
            main_layout.addWidget(btn)

        self.create_project_btn.clicked.connect(self.controller.create_project_action)
        self.load_project_btn.clicked.connect(self.controller.load_project_action)
        self.manage_exclusions_btn.clicked.connect(self.controller.manage_exclusions)
        self.analyze_directory_btn.clicked.connect(self.controller.analyze_directory)
        self.view_directory_tree_btn.clicked.connect(self.controller.view_directory_tree)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self.setGeometry(300, 300, 800, 600)

        self.theme_manager.apply_theme(self)

    def create_styled_button(self, text):
        btn = QPushButton(text)
        btn.setFont(QFont('Arial', 14))
        return btn

    def toggle_theme(self):
        self.controller.toggle_theme()

    def show_dashboard(self):
        self.show()

    def show_project_ui(self):
        self.project_ui = ProjectUI(self.controller)
        self.project_ui.project_created.connect(self.controller.on_project_created)
        self.project_ui.project_loaded.connect(self.controller.on_project_loaded)
        self.project_ui.show()
        return self.project_ui

    def on_project_created(self, project):
        logger.info(f"Project created: {project.name}")
        self.update_project_info(project)
        self.enable_project_actions()

    def on_project_loaded(self, project):
        logger.info(f"Project loaded: {project.name}")
        self.update_project_info(project)
        self.enable_project_actions()

    def enable_project_actions(self):
        self.manage_exclusions_btn.setEnabled(True)
        self.analyze_directory_btn.setEnabled(True)
        self.view_directory_tree_btn.setEnabled(True)

    def show_auto_exclude_ui(self, auto_exclude_manager, settings_manager, formatted_recommendations, project_context):
        if not self.auto_exclude_ui:
            self.auto_exclude_ui = AutoExcludeUI(auto_exclude_manager, settings_manager, formatted_recommendations, project_context)
        self.auto_exclude_ui.show()

    def show_result(self, directory_analyzer):
        if self.controller.project_controller.project_context:
            self.result_ui = ResultUI(self.controller, self.theme_manager, directory_analyzer)
            self.result_ui.show()
            return self.result_ui
        else:
            return None

    def manage_exclusions(self, settings_manager):
        if self.controller.project_controller.project_context:
            self.exclusions_ui = ExclusionsManagerUI(self.controller, self.theme_manager, settings_manager)
            self.exclusions_ui.show()
            return self.exclusions_ui
        else:
            QMessageBox.warning(self, "No Project", "Please load or create a project before managing exclusions.")
            return None

    def view_directory_tree_ui(self, result):
        if not self.directory_tree_ui:
            self.directory_tree_ui = DirectoryTreeUI(self.controller, self.theme_manager)
        self.directory_tree_ui.update_tree(result)
        self.directory_tree_ui.show()



    def update_project_info(self, project):
        self.setWindowTitle(f"GynTree - {project.name}")
        self.status_bar.showMessage(f"Current project: {project.name}, Start directory: {project.start_directory}")

    def clear_directory_tree(self):
        if hasattr(self, 'directory_tree_view'):
            self.directory_tree_view.clear()
        logger.debug("Directory tree cleared")

    def clear_analysis(self):
        if hasattr(self, 'analysis_result_view'):
            self.analysis_result_view.clear()
        logger.debug("Analysis results cleared")

    def clear_exclusions(self):
        if hasattr(self, 'exclusions_list_view'):
            self.exclusions_list_view.clear()
        logger.debug("Exclusions list cleared")

    def show_error_message(self, title, message):
        QMessageBox.critical(self, title, message)