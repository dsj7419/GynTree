import os
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QStatusBar, QHBoxLayout
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt
from components.UI.ProjectUI import ProjectUI
from components.UI.AutoExcludeUI import AutoExcludeUI
from components.UI.ResultUI import ResultUI
from components.UI.DirectoryTreeUI import DirectoryTreeUI
from components.UI.ExclusionsManagerUI import ExclusionsManagerUI
from utilities.resource_path import get_resource_path
import logging

logger = logging.getLogger(__name__)

class DashboardUI(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.project_ui = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('GynTree Dashboard')
        self.setWindowIcon(QIcon(get_resource_path('assets/images/gyntree_logo 64x64.ico')))
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QLabel { color: #333; }
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                border: none; 
                padding: 15px 32px; 
                text-align: center; 
                text-decoration: none; 
                font-size: 16px; 
                margin: 4px 2px; 
                border-radius: 8px; 
            }
            QPushButton:hover { background-color: #45a049; }
            QStatusBar { background-color: #333; color: white; }
        """)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        logo_label = QLabel()
        logo_path = get_resource_path('assets/images/gyntree_logo.png')
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logger.warning(f"Logo file not found at {logo_path}")

        welcome_label = QLabel('Welcome to GynTree!')
        welcome_label.setFont(QFont('Arial', 24, QFont.Bold))

        header_layout = QHBoxLayout()
        header_layout.addWidget(logo_label)
        header_layout.addWidget(welcome_label)
        header_layout.setAlignment(Qt.AlignCenter)
        main_layout.addLayout(header_layout)

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

    def create_styled_button(self, text):
        btn = QPushButton(text)
        btn.setFont(QFont('Arial', 14))
        return btn

    def show_dashboard(self):
        self.show()

    def show_project_ui(self):
        self.project_ui = ProjectUI(self.controller)
        self.project_ui.project_created.connect(self.controller.on_project_created)
        self.project_ui.project_loaded.connect(self.controller.on_project_loaded)
        self.project_ui.show()
        return self.project_ui

    def update_project_info(self, project):
        self.setWindowTitle(f"GynTree - {project.name}")
        self.status_bar.showMessage(f"Current project: {project.name}, Start directory: {project.start_directory}")

    def show_auto_exclude_ui(self, auto_exclude_manager, settings_manager, formatted_recommendations, project_context):
        auto_exclude_ui = AutoExcludeUI(auto_exclude_manager, settings_manager, formatted_recommendations, project_context)
        auto_exclude_ui.show()
        return auto_exclude_ui

    def show_result(self, directory_analyzer):
        result_ui = ResultUI(directory_analyzer)
        result_ui.show()
        return result_ui

    def manage_exclusions(self, settings_manager):
        exclusions_ui = ExclusionsManagerUI(settings_manager)
        exclusions_ui.show()
        return exclusions_ui

    def view_directory_tree(self, result):
        tree_ui = DirectoryTreeUI(result)
        tree_ui.show()
        return tree_ui

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
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)