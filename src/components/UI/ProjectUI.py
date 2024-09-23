from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QListWidget, QHBoxLayout, QFrame, QMessageBox)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from models.Project import Project
from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager
import logging

logger = logging.getLogger(__name__)

class ProjectUI(QWidget):
    project_created = pyqtSignal(object)
    project_loaded = pyqtSignal(object)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.theme_manager = ThemeManager.getInstance()
        self.init_ui()

        self.theme_manager.themeChanged.connect(self.apply_theme)

    def init_ui(self):
        self.setWindowTitle('Project Manager')
        self.setWindowIcon(QIcon(get_resource_path('assets/images/GynTree_logo.ico')))

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        create_section = QFrame()
        create_section.setFrameShape(QFrame.StyledPanel)
        create_layout = QVBoxLayout(create_section)

        create_title = QLabel('Create New Project')
        create_title.setFont(QFont('Arial', 24, QFont.Bold))
        create_layout.addWidget(create_title)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText('Project Name')
        create_layout.addWidget(self.project_name_input)

        dir_layout = QHBoxLayout()
        self.start_dir_button = self.create_styled_button('Select Start Directory')
        self.start_dir_button.clicked.connect(self.select_directory)
        self.start_dir_label = QLabel('No directory selected')
        dir_layout.addWidget(self.start_dir_button)
        dir_layout.addWidget(self.start_dir_label)
        create_layout.addLayout(dir_layout)

        self.create_project_btn = self.create_styled_button('Create Project')
        self.create_project_btn.clicked.connect(self.create_project)
        create_layout.addWidget(self.create_project_btn)

        layout.addWidget(create_section)

        load_section = QFrame()
        load_section.setFrameShape(QFrame.StyledPanel)
        load_layout = QVBoxLayout(load_section)

        load_title = QLabel('Load Existing Project')
        load_title.setFont(QFont('Arial', 24, QFont.Bold))
        load_layout.addWidget(load_title)

        self.project_list = QListWidget()
        self.project_list.addItems(self.controller.project_controller.project_manager.list_projects())
        load_layout.addWidget(self.project_list)

        self.load_project_btn = self.create_styled_button('Load Project')
        self.load_project_btn.clicked.connect(self.load_project)
        load_layout.addWidget(self.load_project_btn)

        layout.addWidget(load_section)

        self.setLayout(layout)
        self.setGeometry(300, 300, 600, 600)

        self.apply_theme()

    def create_styled_button(self, text):
        btn = QPushButton(text)
        btn.setFont(QFont('Arial', 14))
        return btn

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Start Directory")
        if directory:
            self.start_dir_label.setText(directory)

    def create_project(self):
        project_name = self.project_name_input.text()
        start_directory = self.start_dir_label.text()
        if project_name and start_directory != 'No directory selected':
            new_project = Project(name=project_name, start_directory=start_directory)
            logger.info(f"Creating new project: {project_name}")
            self.project_created.emit(new_project)
            self.project_name_input.clear()
            self.start_dir_label.setText('No directory selected')
            self.close()
        else:
            QMessageBox.warning(self, "Invalid Input", "Please provide a project name and select a start directory.")

    def load_project(self):
        selected_items = self.project_list.selectedItems()
        if selected_items:
            project_name = selected_items[0].text()
            logger.info(f"Loading project: {project_name}")
            self.project_loaded.emit(Project(name=project_name, start_directory=""))
            self.close()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a project to load.")

    def apply_theme(self):
        self.theme_manager.apply_theme(self)

    def closeEvent(self, event):
        super().closeEvent(event)