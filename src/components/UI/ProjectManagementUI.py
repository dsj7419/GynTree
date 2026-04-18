import logging
from typing import TYPE_CHECKING, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QFont, QIcon, QShowEvent
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager

if TYPE_CHECKING:
    from controllers.AppController import AppController

logger = logging.getLogger(__name__)


class ProjectManagementUI(QMainWindow):
    project_deleted = pyqtSignal(str)

    def __init__(
        self, controller: "AppController", theme_manager: Optional[ThemeManager] = None
    ) -> None:
        super().__init__()
        self.controller = controller
        self.theme_manager = theme_manager or ThemeManager.getInstance()
        self.project_list: Optional[QListWidget] = None
        self.delete_button: Optional[QPushButton] = None

        self.init_ui()

        self.theme_manager.themeChanged.connect(self.apply_theme)
        self.apply_theme()

    def init_ui(self) -> None:
        self.setWindowTitle("Project Management")
        self.setWindowIcon(QIcon(get_resource_path("assets/images/GynTree_logo.ico")))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        header = QLabel("Manage Projects")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        description = QLabel("Select a project to manage:")
        description.setFont(QFont("Arial", 12))
        layout.addWidget(description)

        self.project_list = QListWidget()
        self.project_list.setAlternatingRowColors(True)
        self.project_list.setFont(QFont("Arial", 11))
        self.project_list.setMinimumHeight(200)
        layout.addWidget(self.project_list)

        button_container = QFrame()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(15)

        button_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        self.delete_button = self.create_styled_button("Delete Project", "critical")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete_project)
        button_layout.addWidget(self.delete_button)

        refresh_button = self.create_styled_button("Refresh List")
        refresh_button.clicked.connect(self.refresh_project_list)
        button_layout.addWidget(refresh_button)

        close_button = self.create_styled_button("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        button_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        layout.addWidget(button_container)

        self.project_list.itemSelectionChanged.connect(self.on_selection_changed)

        self.setMinimumSize(500, 400)
        self.setGeometry(300, 300, 600, 500)

        self.load_projects()

    def create_styled_button(self, text: str, style: str = "normal") -> QPushButton:
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 12))
        btn.setMinimumWidth(120)

        if style == "critical":
            btn.setProperty("class", "critical")

        return btn

    def load_projects(self) -> None:
        try:
            if self.project_list is None:  # Changed from if not self.project_list
                logger.error("Project list widget is not initialized")
                return

            projects = (
                self.controller.project_controller.project_manager.list_projects()
            )
            logger.debug(f"ProjectManagementUI: Found {len(projects)} projects")

            self.project_list.clear()
            for project_name in sorted(projects):
                item = QListWidgetItem(project_name)
                item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.project_list.addItem(item)

            logger.debug(
                f"ProjectManagementUI: List now has {self.project_list.count()} items"
            )
            self.project_list.update()

            if self.delete_button:
                self.delete_button.setEnabled(False)

        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")
            QMessageBox.critical(self, "Error", "Failed to load projects list")

    def refresh_project_list(self) -> None:
        try:
            logger.debug("Refreshing project list")
            if self.project_list:  # Add type check
                self.load_projects()
        except Exception as e:
            logger.error(f"Error refreshing project list: {str(e)}")
            QMessageBox.critical(self, "Error", "Failed to refresh project list")

    def on_selection_changed(self) -> None:
        if self.delete_button and self.project_list:
            selected = bool(self.project_list.selectedItems())
            self.delete_button.setEnabled(selected)
            if selected:
                items = self.project_list.selectedItems()
                if items:  # Add type check
                    logger.debug(f"Selected project: {items[0].text()}")

    def delete_project(self) -> None:
        if not self.project_list:
            return

        selected_items = self.project_list.selectedItems()
        if not selected_items:
            return

        project_name = selected_items[0].text()
        logger.debug(f"Attempting to delete project: {project_name}")

        if (
            self.controller.project_controller.current_project
            and self.controller.project_controller.current_project.name.lower()
            == project_name.lower()
        ):
            QMessageBox.warning(
                self,
                "Project In Use",
                "Cannot delete the loaded project. Please load a different project first.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f'Are you sure you want to delete the project "{project_name}"?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                success = (
                    self.controller.project_controller.project_manager.delete_project(
                        project_name
                    )
                )
                if success:
                    logger.info(f"Successfully deleted project: {project_name}")
                    self.project_deleted.emit(project_name)
                    self.refresh_project_list()
                    QMessageBox.information(
                        self,
                        "Success",
                        f'Project "{project_name}" has been deleted successfully.',
                    )
                else:
                    logger.error(f"Failed to delete project: {project_name}")
                    QMessageBox.critical(
                        self, "Error", f'Failed to delete project "{project_name}".'
                    )
            except Exception as e:
                logger.error(f"Error deleting project {project_name}: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An error occurred while deleting the project: {str(e)}",
                )

    def apply_theme(self) -> None:
        try:
            self.theme_manager.apply_theme(self)
        except Exception as e:
            logger.error(f"Error applying theme: {str(e)}")

    def closeEvent(self, event: "QCloseEvent") -> None:
        try:
            super().closeEvent(event)
        except Exception as e:
            logger.error(f"Error handling close event: {str(e)}")

    def showEvent(self, event: "QShowEvent") -> None:
        try:
            super().showEvent(event)
            self.refresh_project_list()
        except Exception as e:
            logger.error(f"Error handling show event: {str(e)}")
