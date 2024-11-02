from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                           QLabel, QPushButton, QListWidget, QListWidgetItem,
                           QMessageBox, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, pyqtSignal
import logging
from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager

logger = logging.getLogger(__name__)

class ProjectManagementUI(QMainWindow):
    project_deleted = pyqtSignal(str)  # Emits project name when deleted

    def __init__(self, controller, theme_manager=None):
        super().__init__()
        self.controller = controller
        self.theme_manager = theme_manager or ThemeManager.getInstance()
        self.project_list = None
        self.delete_button = None
        
        # Initialize UI first
        self.init_ui()
        
        # Then connect theme changes and apply theme
        self.theme_manager.themeChanged.connect(self.apply_theme)
        self.apply_theme()

    def init_ui(self):
        """Initialize the user interface."""
        try:
            self.setWindowTitle('Project Management')
            self.setWindowIcon(QIcon(get_resource_path('assets/images/GynTree_logo.ico')))

            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            layout.setContentsMargins(30, 30, 30, 30)
            layout.setSpacing(20)

            # Header
            header = QLabel('Manage Projects')
            header.setFont(QFont('Arial', 24, QFont.Bold))
            header.setAlignment(Qt.AlignCenter)
            layout.addWidget(header)

            # Description
            description = QLabel('Select a project to manage:')
            description.setFont(QFont('Arial', 12))
            layout.addWidget(description)

            # Initialize project list
            self.project_list = QListWidget()
            self.project_list.setAlternatingRowColors(True)
            self.project_list.setFont(QFont('Arial', 11))
            self.project_list.setMinimumHeight(200)
            layout.addWidget(self.project_list)

            # Buttons Container
            button_container = QFrame()
            button_layout = QHBoxLayout(button_container)
            button_layout.setSpacing(15)

            # Add spacer to push buttons to center
            button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

            # Delete Button
            self.delete_button = self.create_styled_button('Delete Project', 'critical')
            self.delete_button.setEnabled(False)  # Disabled until selection
            self.delete_button.clicked.connect(self.delete_project)
            button_layout.addWidget(self.delete_button)

            # Refresh Button
            refresh_button = self.create_styled_button('Refresh List')
            refresh_button.clicked.connect(self.refresh_project_list)
            button_layout.addWidget(refresh_button)

            # Close Button
            close_button = self.create_styled_button('Close')
            close_button.clicked.connect(self.close)
            button_layout.addWidget(close_button)

            # Add spacer to push buttons to center
            button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

            layout.addWidget(button_container)

            # Connect selection changed signal
            self.project_list.itemSelectionChanged.connect(self.on_selection_changed)

            # Set window properties
            self.setMinimumSize(500, 400)
            self.setGeometry(300, 300, 600, 500)

            # Load initial project list
            self.load_projects()

        except Exception as e:
            logger.error(f"Error initializing UI: {str(e)}")
            raise

    def create_styled_button(self, text, style='normal'):
        """Create a styled button with the given text and style."""
        btn = QPushButton(text)
        btn.setFont(QFont('Arial', 12))
        btn.setMinimumWidth(120)
        
        if style == 'critical':
            btn.setProperty('class', 'critical')
        
        return btn

    def load_projects(self):
        """Load the initial list of projects."""
        try:
            projects = self.controller.project_controller.project_manager.list_projects()
            logger.debug(f"Found {len(projects)} projects")
            
            self.project_list.clear()
            for project_name in sorted(projects):
                item = QListWidgetItem(project_name)
                item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.project_list.addItem(item)
                
            if self.delete_button:
                self.delete_button.setEnabled(False)

        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")
            QMessageBox.critical(self, "Error", "Failed to load projects list")

    def refresh_project_list(self):
        """Refresh the list of projects."""
        try:
            logger.debug("Refreshing project list")
            self.load_projects()
        except Exception as e:
            logger.error(f"Error refreshing project list: {str(e)}")
            QMessageBox.critical(self, "Error", "Failed to refresh project list")

    def on_selection_changed(self):
        """Handle selection changes in the project list."""
        if self.delete_button:
            selected = len(self.project_list.selectedItems()) > 0
            self.delete_button.setEnabled(selected)
            if selected:
                logger.debug(f"Selected project: {self.project_list.selectedItems()[0].text()}")

    def delete_project(self):
        """Delete the selected project after confirmation."""
        selected_items = self.project_list.selectedItems()
        if not selected_items:
            return

        project_name = selected_items[0].text()
        logger.debug(f"Attempting to delete project: {project_name}")
        
        # Check if project is currently loaded
        if (self.controller.project_controller.current_project and 
            self.controller.project_controller.current_project.name.lower() == project_name.lower()):
            QMessageBox.warning(
                self,
                "Project In Use",
                "Cannot delete the currently loaded project. Please load a different project first."
            )
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            'Confirm Deletion',
            f'Are you sure you want to delete the project "{project_name}"?\n\nThis action cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success = self.controller.project_controller.project_manager.delete_project(project_name)
                if success:
                    logger.info(f"Successfully deleted project: {project_name}")
                    self.project_deleted.emit(project_name)
                    self.refresh_project_list()
                    QMessageBox.information(
                        self,
                        "Success",
                        f'Project "{project_name}" has been deleted successfully.'
                    )
                else:
                    logger.error(f"Failed to delete project: {project_name}")
                    QMessageBox.critical(
                        self,
                        "Error",
                        f'Failed to delete project "{project_name}".'
                    )
            except Exception as e:
                logger.error(f"Error deleting project {project_name}: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f'An error occurred while deleting the project: {str(e)}'
                )

    def apply_theme(self):
        """Apply the current theme to the UI."""
        try:
            self.theme_manager.apply_theme(self)
        except Exception as e:
            logger.error(f"Error applying theme: {str(e)}")

    def closeEvent(self, event):
        """Handle window close event."""
        try:
            super().closeEvent(event)
        except Exception as e:
            logger.error(f"Error handling close event: {str(e)}")

    def showEvent(self, event):
        """Handle window show event."""
        try:
            super().showEvent(event)
            # Refresh the project list when the window is shown
            self.refresh_project_list()
        except Exception as e:
            logger.error(f"Error handling show event: {str(e)}")