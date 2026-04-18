import logging
import os
from typing import TYPE_CHECKING, List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCloseEvent, QFont, QIcon, QShowEvent
from PyQt5.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.SettingsManager import SettingsManager
from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager

if TYPE_CHECKING:
    from controllers.AppController import AppController

logger = logging.getLogger(__name__)


class ExclusionsManagerUI(QWidget):
    def __init__(
        self,
        controller: "AppController",
        theme_manager: ThemeManager,
        settings_manager: SettingsManager,
    ) -> None:
        super().__init__()
        self.controller = controller
        self.theme_manager = theme_manager
        self.settings_manager = settings_manager
        self.exclusion_tree: QTreeWidget = QTreeWidget()
        self.root_tree: QTreeWidget = QTreeWidget()
        self._skip_show_event: bool = False

        self.setWindowTitle("Exclusions Manager")
        self.setWindowIcon(QIcon(get_resource_path("assets/images/GynTree_logo.ico")))

        self.init_ui()
        self.theme_manager.themeChanged.connect(self.apply_theme)

    def init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Manage Exclusions")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        splitter = QSplitter(Qt.Vertical)

        root_group = QGroupBox("Root Exclusions (Non-editable)")
        root_layout = QVBoxLayout()
        self.root_tree.setHeaderLabels(["Excluded Paths"])
        self.root_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        root_layout.addWidget(self.root_tree)
        root_group.setLayout(root_layout)
        splitter.addWidget(root_group)

        detailed_group = QGroupBox("Detailed Exclusions")
        detailed_layout = QVBoxLayout()
        self.exclusion_tree.setHeaderLabels(["Type", "Path"])
        self.exclusion_tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.exclusion_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        detailed_layout.addWidget(self.exclusion_tree)
        detailed_group.setLayout(detailed_layout)
        splitter.addWidget(detailed_group)

        layout.addWidget(splitter)

        buttons_layout = QHBoxLayout()
        add_dir_button = QPushButton("Add Directory")
        add_file_button = QPushButton("Add File")
        remove_button = QPushButton("Remove Selected")
        buttons_layout.addWidget(add_dir_button)
        buttons_layout.addWidget(add_file_button)
        buttons_layout.addWidget(remove_button)
        layout.addLayout(buttons_layout)

        save_button = QPushButton("Save & Exit")
        save_button.clicked.connect(self.save_and_exit)
        layout.addWidget(save_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setGeometry(400, 300, 800, 600)

        add_dir_button.clicked.connect(self.add_directory)
        add_file_button.clicked.connect(self.add_file)
        remove_button.clicked.connect(self.remove_selected)

        self.apply_theme()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not self._skip_show_event:
            self.load_project_data()

    def load_project_data(self) -> None:
        if (
            self.controller.project_controller.project_context
            and self.controller.project_controller.project_context.is_initialized
        ):
            self.settings_manager = (
                self.controller.project_controller.project_context.settings_manager
            )
            self.populate_exclusion_tree()
            self.populate_root_exclusions()
        else:
            QMessageBox.warning(
                self,
                "No Project",
                "No project is currently loaded. Please load or create a project first.",
            )

    def populate_root_exclusions(self) -> None:
        self.root_tree.clear()
        if self.settings_manager:
            root_exclusions = self.settings_manager.get_root_exclusions()
            for path in sorted(root_exclusions):
                item = QTreeWidgetItem(self.root_tree)
                item.setText(0, path)
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
            self.root_tree.expandAll()

    def add_directory(self) -> None:
        if not self.settings_manager:
            QMessageBox.warning(self, "No Project", "No project is currently loaded.")
            return

        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory to Exclude"
        )
        if directory:
            relative_directory = os.path.relpath(
                directory,
                self.controller.project_controller.project_context.project.start_directory,
            )
            exclusions = self.settings_manager.get_all_exclusions()
            excluded_dirs = set(exclusions.get("excluded_dirs", set()))
            root_exclusions = set(exclusions.get("root_exclusions", set()))

            if (
                relative_directory not in excluded_dirs
                and relative_directory not in root_exclusions
            ):
                excluded_dirs.add(relative_directory)
                self.settings_manager.update_settings(
                    {"excluded_dirs": list(excluded_dirs)}
                )
                self.populate_exclusion_tree()
            else:
                QMessageBox.warning(
                    self,
                    "Duplicate Entry",
                    f"The directory '{relative_directory}' is already excluded.",
                )

    def add_file(self) -> None:
        if not self.settings_manager:
            QMessageBox.warning(self, "No Project", "No project is currently loaded.")
            return

        file, _ = QFileDialog.getOpenFileName(self, "Select File to Exclude")
        if file:
            relative_file = os.path.relpath(
                file,
                self.controller.project_controller.project_context.project.start_directory,
            )
            exclusions = self.settings_manager.get_all_exclusions()
            excluded_files = set(exclusions.get("excluded_files", set()))
            root_exclusions = set(exclusions.get("root_exclusions", set()))

            if relative_file not in excluded_files and not any(
                relative_file.startswith(root_dir) for root_dir in root_exclusions
            ):
                excluded_files.add(relative_file)
                self.settings_manager.update_settings(
                    {"excluded_files": list(excluded_files)}
                )
                self.populate_exclusion_tree()
            else:
                QMessageBox.warning(
                    self,
                    "Duplicate Entry",
                    f"The file '{relative_file}' is already excluded or within a root exclusion.",
                )

    def remove_selected(self) -> None:
        if not self.settings_manager:
            QMessageBox.warning(self, "No Project", "No project is currently loaded.")
            return

        selected_items = self.exclusion_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(
                self, "No Selection", "Please select an exclusion to remove."
            )
            return

        exclusions = self.settings_manager.get_all_exclusions()
        excluded_dirs = set(exclusions.get("excluded_dirs", set()))
        excluded_files = set(exclusions.get("excluded_files", set()))
        updated = False

        for item in selected_items:
            parent = item.parent()
            if parent:
                path = item.text(1)
                category = parent.text(0)
                if category == "Excluded Dirs" and path in excluded_dirs:
                    excluded_dirs.remove(path)
                    updated = True
                elif category == "Excluded Files" and path in excluded_files:
                    excluded_files.remove(path)
                    updated = True

        if updated:
            self.settings_manager.update_settings(
                {
                    "excluded_dirs": list(excluded_dirs),
                    "excluded_files": list(excluded_files),
                }
            )
            self.populate_exclusion_tree()

    def populate_exclusion_tree(self) -> None:
        self.exclusion_tree.clear()
        if self.settings_manager:
            exclusions = self.settings_manager.get_all_exclusions()

            dirs_item = QTreeWidgetItem(self.exclusion_tree)
            dirs_item.setText(0, "Excluded Dirs")
            dirs_item.setFlags(dirs_item.flags() & ~Qt.ItemIsSelectable)

            for directory in sorted(exclusions.get("excluded_dirs", set())):
                child = QTreeWidgetItem(dirs_item)
                child.setText(0, "Directory")
                child.setText(1, str(directory))
                child.setFlags(child.flags() | Qt.ItemIsSelectable | Qt.ItemIsEditable)

            files_item = QTreeWidgetItem(self.exclusion_tree)
            files_item.setText(0, "Excluded Files")
            files_item.setFlags(files_item.flags() & ~Qt.ItemIsSelectable)

            for file in sorted(exclusions.get("excluded_files", set())):
                child = QTreeWidgetItem(files_item)
                child.setText(0, "File")
                child.setText(1, str(file))
                child.setFlags(child.flags() | Qt.ItemIsSelectable | Qt.ItemIsEditable)

            self.exclusion_tree.expandAll()

    def save_and_exit(self) -> None:
        if not self.settings_manager:
            QMessageBox.warning(
                self, "Error", "No project loaded. Cannot save exclusions."
            )
            return

        try:
            root_exclusions: List[str] = []
            for i in range(self.root_tree.topLevelItemCount()):
                item = self.root_tree.topLevelItem(i)
                if item:
                    root_exclusions.append(item.text(0))

            excluded_dirs: List[str] = []
            dirs_item = self.exclusion_tree.topLevelItem(0)
            if dirs_item:
                for i in range(dirs_item.childCount()):
                    child = dirs_item.child(i)
                    if child:
                        excluded_dirs.append(child.text(1))

            excluded_files: List[str] = []
            files_item = self.exclusion_tree.topLevelItem(1)
            if files_item:
                for i in range(files_item.childCount()):
                    child = files_item.child(i)
                    if child:
                        excluded_files.append(child.text(1))

            self.settings_manager.update_settings(
                {
                    "root_exclusions": root_exclusions,
                    "excluded_dirs": excluded_dirs,
                    "excluded_files": excluded_files,
                }
            )
            self.settings_manager.save_settings()
            self.close()
        except Exception as e:
            logger.error(f"Error saving exclusions: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to save exclusions: {str(e)}")

    def apply_theme(self) -> None:
        self.theme_manager.apply_theme(self)

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)
