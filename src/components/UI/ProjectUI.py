from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QListWidget, QHBoxLayout, QFrame, QMessageBox)
from PyQt5.QtGui import QIcon, QFont, QCloseEvent
from PyQt5.QtCore import Qt, pyqtSignal
from models.Project import Project
from utilities.error_handler import handle_exception
from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager
from pathlib import Path
import logging
import re
import os

logger = logging.getLogger(__name__)

class ProjectUI(QWidget):
    project_created = pyqtSignal(object)
    project_loaded = pyqtSignal(object)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.theme_manager = ThemeManager.getInstance()
        self.init_ui()
        
        # Connect theme changes
        self.theme_manager.themeChanged.connect(self.apply_theme)

    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle('Project Manager')
        self.setWindowIcon(QIcon(get_resource_path('assets/images/GynTree_logo.ico')))

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Create Project Section
        create_section = QFrame(self)
        create_section.setObjectName("createSection")
        create_section.setFrameShape(QFrame.StyledPanel)
        create_section.setFrameShadow(QFrame.Raised)
        create_layout = QVBoxLayout(create_section)

        create_title = QLabel('Create New Project')
        create_title.setFont(QFont('Arial', 24, QFont.Bold))
        create_layout.addWidget(create_title)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText('Project Name')
        self.project_name_input.setMaxLength(255)
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

        main_layout.addWidget(create_section)

        # Load Project Section
        load_section = QFrame(self)
        load_section.setObjectName("loadSection")
        load_section.setFrameShape(QFrame.StyledPanel)
        load_section.setFrameShadow(QFrame.Raised)
        load_layout = QVBoxLayout(load_section)

        load_title = QLabel('Load Existing Project')
        load_title.setFont(QFont('Arial', 24, QFont.Bold))
        load_layout.addWidget(load_title)

        self.project_list = QListWidget()
        self.refresh_project_list()
        load_layout.addWidget(self.project_list)

        self.load_project_btn = self.create_styled_button('Load Project')
        self.load_project_btn.clicked.connect(self.load_project)
        load_layout.addWidget(self.load_project_btn)

        main_layout.addWidget(load_section)

        self.setLayout(main_layout)
        self.setGeometry(300, 300, 600, 600)
        self.apply_theme()

    def create_styled_button(self, text):
        """Create a styled button with consistent appearance"""
        btn = QPushButton(text)
        btn.setFont(QFont('Arial', 14))
        return btn

    def refresh_project_list(self):
        """Refresh the list of available projects"""
        self.project_list.clear()
        projects = self.controller.project_controller.project_manager.list_projects()
        self.project_list.addItems(projects)

    def select_directory(self):
        """Handle directory selection"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Start Directory",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if directory:
            self.start_dir_label.setText(directory)

    def validate_project_name(self, name):
        """Validate project name for illegal characters and length"""
        if not name:
            return False, "Project name cannot be empty"
        
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, name):
            return False, "Project name contains invalid characters"
            
        if len(name) > 255:
            return False, "Project name is too long"
            
        return True, ""

    def validate_directory(self, directory):
        """Validate selected directory"""
        if directory == 'No directory selected':
            return False, "Please select a directory"
            
        try:
            path = Path(directory)
            if not path.exists():
                return False, "Selected directory does not exist"
                
            if not path.is_dir():
                return False, "Selected path is not a directory"
                
            # Check if directory is readable
            if not os.access(path, os.R_OK):
                return False, "Directory is not accessible"
                
            return True, ""
        except Exception as e:
            return False, f"Invalid directory path: {str(e)}"

    @handle_exception
    def create_project(self, *args):
        """
        Handle project creation with validation.
        
        Args:
            *args: Variable arguments to support signal connection
        """
        project_name = self.project_name_input.text().strip()
        start_directory = self.start_dir_label.text()

        # Validate project name
        name_valid, name_error = self.validate_project_name(project_name)
        if not name_valid:
            QMessageBox.warning(self, "Invalid Project Name", name_error)
            return

        # Validate directory
        dir_valid, dir_error = self.validate_directory(start_directory)
        if not dir_valid:
            QMessageBox.warning(self, "Invalid Directory", dir_error)
            return

        try:
            new_project = Project(name=project_name, start_directory=start_directory)
            logger.info(f"Creating new project: {project_name}")
            
            # Emit the signal
            self.project_created.emit(new_project)
            
            # Clear inputs
            self.project_name_input.clear()
            self.start_dir_label.setText('No directory selected')
            
            # Close the window
            self.close()
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to create project: {str(e)}")

    def load_project(self):
        """Handle project loading with proper validation."""
        selected_items = self.project_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a project to load.")
            return

        try:
            project_name = selected_items[0].text()
            logger.info(f"Loading project: {project_name}")
            
            # Load the project from the controller
            loaded_project = self.controller.project_controller.load_project(project_name)
            if loaded_project:
                logger.info(f"Successfully loaded project: {loaded_project.name}")
                self.project_loaded.emit(loaded_project)
                self.close()
            else:
                raise ValueError(f"Failed to load project {project_name}")
                
        except Exception as e:
            logger.error(f"Error loading project: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load project: {str(e)}")

    def apply_theme(self):
        """Apply current theme to the UI"""
        if self.theme_manager:
            self.theme_manager.apply_theme(self)

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        event.accept()
        super().closeEvent(event) 