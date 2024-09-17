# GynTree: This file defines the DashboardUI class, which serves as the main interface for the GynTree application.

from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, 
                             QStatusBar, QHBoxLayout)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt
from components.UI.AutoExcludeUI import AutoExcludeUI
from components.UI.ProjectUI import ProjectUI
from components.UI.ExclusionsManager import ExclusionsManager
from components.UI.ResultUI import ResultUI
from components.UI.DirectoryTreeUI import DirectoryTreeUI
import os

class DashboardUI(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.auto_exclude_ui_instance = None
        self.exclusions_manager_instance = None
        self.result_ui_instance = None
        self.directory_tree_instance = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('GynTree Dashboard')
        self.setWindowIcon(QIcon('assets/images/GynTree_logo 64X64.ico'))
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                color: #333;
            }
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
            QPushButton:hover {
                background-color: #45a049;
            }
            QStatusBar {
                background-color: #333;
                color: white;
            }
        """)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Logo and welcome message
        logo_label = QLabel()
        logo_path = 'assets/images/GynTree_logo.png'
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            print(f"Warning: Logo file not found at {logo_path}")
        welcome_label = QLabel('Welcome to GynTree!')
        welcome_label.setFont(QFont('Arial', 24, QFont.Bold))
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(logo_label)
        header_layout.addWidget(welcome_label)
        header_layout.setAlignment(Qt.AlignCenter)
        main_layout.addLayout(header_layout)

        # Buttons
        self.create_project_btn = self.create_styled_button('Create Project')
        self.load_project_btn = self.create_styled_button('Load Project')
        self.manage_exclusions_btn = self.create_styled_button('Manage Exclusions')
        self.analyze_directory_btn = self.create_styled_button('Analyze Directory')
        self.view_directory_tree_btn = self.create_styled_button('View Directory Tree')

        for btn in [self.create_project_btn, self.load_project_btn, self.manage_exclusions_btn,
                    self.analyze_directory_btn, self.view_directory_tree_btn]:
            main_layout.addWidget(btn)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self.create_project_btn.clicked.connect(self.controller.create_project)
        self.load_project_btn.clicked.connect(self.controller.load_project)
        self.manage_exclusions_btn.clicked.connect(self.controller.manage_exclusions)
        self.analyze_directory_btn.clicked.connect(self.controller.analyze_directory)
        self.view_directory_tree_btn.clicked.connect(self.controller.view_directory_tree)

        self.setGeometry(300, 300, 600, 500)

    def create_styled_button(self, text):
        btn = QPushButton(text)
        btn.setFont(QFont('Arial', 14))
        return btn

    def show_dashboard(self):
        self.show()

    def update_project_info(self, project):
        self.setWindowTitle(f"GynTree - {project.name}")
        self.status_bar.showMessage(f"Current Project: {project.name}, Start Directory: {project.start_directory}")

    def show_project_ui(self):
        project_ui = ProjectUI()
        project_ui.show()
        return project_ui
    
    def show_result(self, result):
        if not self.result_ui_instance:
            self.result_ui_instance = ResultUI()
        self.result_ui_instance.update_result(result)
        self.result_ui_instance.show()

    def show_auto_exclude_ui(self, auto_exclude_manager, settings_manager):
        if not self.auto_exclude_ui_instance:
            self.auto_exclude_ui_instance = AutoExcludeUI(auto_exclude_manager, settings_manager)
        self.auto_exclude_ui_instance.show()

    def manage_exclusions(self, settings_manager):
        if not self.exclusions_manager_instance:
            self.exclusions_manager_instance = ExclusionsManager(settings_manager)
        self.exclusions_manager_instance.show()

    def view_directory_tree(self, directory_analyzer):
        if not self.directory_tree_instance:
            self.directory_tree_instance = DirectoryTreeUI(directory_analyzer)
        self.directory_tree_instance.show()