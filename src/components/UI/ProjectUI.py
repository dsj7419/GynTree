from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QListWidget, QHBoxLayout, QFrame)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from models.Project import Project
from services.ProjectManager import ProjectManager

class ProjectUI(QWidget):
    def __init__(self):
        super().__init__()
        self.project_manager = ProjectManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Project Manager')
        self.setWindowIcon(QIcon('assets/images/GynTree_logo 64X64.ico'))
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: #333;
            }
            QLabel {
                font-size: 16px;
                color: #333;
            }
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Create project section
        create_section = QFrame()
        create_section.setFrameShape(QFrame.StyledPanel)
        create_layout = QVBoxLayout(create_section)

        create_title = QLabel('Create New Project')
        create_title.setFont(QFont('Arial', 18, QFont.Bold))
        create_layout.addWidget(create_title)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText('Project Name')
        create_layout.addWidget(self.project_name_input)

        dir_layout = QHBoxLayout()
        self.start_dir_button = QPushButton('Select Start Directory')
        self.start_dir_button.clicked.connect(self.select_directory)
        self.start_dir_label = QLabel('No directory selected')
        dir_layout.addWidget(self.start_dir_button)
        dir_layout.addWidget(self.start_dir_label)
        create_layout.addLayout(dir_layout)

        self.create_project_btn = QPushButton('Create Project')
        create_layout.addWidget(self.create_project_btn)

        layout.addWidget(create_section)

        # Load project section
        load_section = QFrame()
        load_section.setFrameShape(QFrame.StyledPanel)
        load_layout = QVBoxLayout(load_section)

        load_title = QLabel('Load Existing Project')
        load_title.setFont(QFont('Arial', 18, QFont.Bold))
        load_layout.addWidget(load_title)

        self.project_list = QListWidget()
        self.project_list.addItems(self.project_manager.list_projects())
        load_layout.addWidget(self.project_list)

        self.load_project_btn = QPushButton('Load Project')
        load_layout.addWidget(self.load_project_btn)

        layout.addWidget(load_section)

        self.setLayout(layout)
        self.setGeometry(300, 300, 500, 600)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Start Directory')
        if directory:
            self.start_dir_label.setText(directory)

    def create_project(self):
        project_name = self.project_name_input.text()
        start_directory = self.start_dir_label.text()
        if project_name and start_directory != 'No directory selected':
            project = Project(name=project_name, start_directory=start_directory)
            self.project_manager.save_project(project)
            self.project_list.addItem(project_name)
            self.project_name_input.clear()
            self.start_dir_label.setText('No directory selected')
            return project
        return None

    def load_project(self):
        selected_items = self.project_list.selectedItems()
        if selected_items:
            project_name = selected_items[0].text()
            project = self.project_manager.load_project(project_name)
            return project
        return None