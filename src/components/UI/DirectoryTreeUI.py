import logging
from typing import Any, Dict, Optional

from PyQt5.QtCore import QSize, Qt, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from components.TreeExporter import TreeExporter
from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class DirectoryTreeUI(QWidget):
    def __init__(self, controller: Any, theme_manager: ThemeManager) -> None:
        super().__init__()
        self.controller = controller
        self.theme_manager = theme_manager
        self.directory_structure: Optional[Dict[str, Any]] = None
        self.folder_icon: QIcon = QIcon()
        self.file_icon: QIcon = QIcon()
        self.tree_widget: Optional[QTreeWidget] = None
        self.tree_exporter: Optional[TreeExporter] = None
        self._load_icons()
        self.init_ui()
        self.theme_manager.themeChanged.connect(self.apply_theme)

    def _load_icons(self) -> None:
        try:
            self.folder_icon = QIcon(get_resource_path("assets/images/folder_icon.png"))
            self.file_icon = QIcon(get_resource_path("assets/images/file_icon.png"))
        except Exception as e:
            logger.error(f"Failed to load icons: {str(e)}")
            self.folder_icon = QIcon()
            self.file_icon = QIcon()

    def create_styled_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 12))
        btn.setMinimumWidth(100)
        btn.setMinimumHeight(30)
        return btn

    def init_ui(self) -> None:
        try:
            self.setWindowTitle("Directory Tree")
            self.setGeometry(300, 150, 800, 600)

            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(30, 30, 30, 30)
            main_layout.setSpacing(20)

            header_layout = self._create_header_layout()
            main_layout.addLayout(header_layout)

            self._setup_tree_widget()
            if self.tree_widget:
                main_layout.addWidget(self.tree_widget)

            self._setup_exporter()
            self.setLayout(main_layout)
            self.apply_theme()

        except Exception as e:
            logger.error(f"Failed to initialize UI: {str(e)}")
            QMessageBox.critical(self, "Error", "Failed to initialize UI components")

    def _create_header_layout(self) -> QHBoxLayout:
        header_layout = QHBoxLayout()
        try:
            title_label = QLabel("Directory Tree")
            title_font = QFont("Arial", 24)
            title_font.setBold(True)
            title_label.setFont(title_font)
            header_layout.addWidget(title_label)

            buttons = {
                "Collapse All": self._handle_collapse_all,
                "Expand All": self._handle_expand_all,
                "Export PNG": self._handle_export_png,
                "Export ASCII": self._handle_export_ascii,
            }

            for text, handler in buttons.items():
                btn = self.create_styled_button(text)
                btn.clicked.connect(handler)
                header_layout.addWidget(btn)

            header_layout.setAlignment(Qt.AlignCenter)
        except Exception as e:
            logger.error(f"Failed to create header layout: {str(e)}")
        return header_layout

    def _setup_tree_widget(self) -> None:
        try:
            self.tree_widget = QTreeWidget()
            if self.tree_widget:
                self.tree_widget.setHeaderLabels(["Name"])
                self.tree_widget.setColumnWidth(0, 300)
                self.tree_widget.setAlternatingRowColors(True)
                self.tree_widget.setIconSize(QSize(20, 20))
                self.tree_widget.header().setSectionResizeMode(
                    0, QHeaderView.ResizeToContents
                )
        except Exception as e:
            logger.error(f"Failed to setup tree widget: {str(e)}")
            self.tree_widget = None

    def _setup_exporter(self) -> None:
        try:
            if self.tree_widget:
                self.tree_exporter = TreeExporter(self.tree_widget)
        except Exception as e:
            logger.error(f"Failed to initialize TreeExporter: {str(e)}")
            self.tree_exporter = None
            QMessageBox.warning(self, "Warning", "Export functionality unavailable")

    @pyqtSlot()
    def _handle_collapse_all(self) -> None:
        try:
            if self.tree_widget:
                self.tree_widget.collapseAll()
        except Exception as e:
            logger.error(f"Error during collapse all: {str(e)}")

    @pyqtSlot()
    def _handle_expand_all(self) -> None:
        try:
            if self.tree_widget:
                self.tree_widget.expandAll()
        except Exception as e:
            logger.error(f"Error during expand all: {str(e)}")

    @pyqtSlot()
    def _handle_export_png(self) -> bool:
        try:
            if not self.tree_widget or not self.tree_exporter:
                QMessageBox.warning(
                    self, "Export Error", "Export functionality not available"
                )
                return False

            if self.tree_widget.topLevelItemCount() == 0:
                result = QMessageBox.warning(
                    self,
                    "Empty Tree",
                    "The directory tree is empty. Do you want to proceed?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if result == QMessageBox.Yes:
                    return bool(self.tree_exporter.export_as_image())
                return False

            return bool(self.tree_exporter.export_as_image())

        except Exception as e:
            logger.error(f"Error during PNG export: {str(e)}")
            QMessageBox.warning(self, "Export Error", "Failed to export as PNG")
            return False

    @pyqtSlot()
    def _handle_export_ascii(self) -> bool:
        try:
            if not self.tree_widget or not self.tree_exporter:
                QMessageBox.warning(
                    self, "Export Error", "Export functionality not available"
                )
                return False

            if self.tree_widget.topLevelItemCount() == 0:
                result = QMessageBox.warning(
                    self,
                    "Empty Tree",
                    "The directory tree is empty. Do you want to proceed?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if result == QMessageBox.Yes:
                    file_name, _ = QFileDialog.getSaveFileName(
                        self, "Export ASCII", "", "Text Files (*.txt)"
                    )
                    if file_name and self.tree_exporter:
                        return bool(self.tree_exporter.export_as_ascii())
                return False

            return bool(self.tree_exporter.export_as_ascii())

        except Exception as e:
            logger.error(f"Error during ASCII export: {str(e)}")
            QMessageBox.warning(self, "Export Error", "Failed to export as ASCII")
            return False

    def update_tree(self, directory_structure: Optional[Dict[str, Any]]) -> None:
        try:
            if not self.tree_widget or not directory_structure:
                return

            self.directory_structure = directory_structure
            self.tree_widget.clear()
            self._populate_tree(
                self.tree_widget.invisibleRootItem(), directory_structure
            )
            self.tree_widget.expandAll()
        except Exception as e:
            logger.error(f"Error updating tree: {str(e)}")
            QMessageBox.warning(self, "Update Error", "Failed to update directory tree")

    def _populate_tree(self, parent: QTreeWidgetItem, data: Dict[str, Any]) -> None:
        try:
            item = QTreeWidgetItem(parent)
            item.setText(0, data["name"])

            icon = self.folder_icon if data["type"] == "directory" else self.file_icon
            if not icon.isNull():
                item.setIcon(0, icon)

            if "children" in data and isinstance(data["children"], list):
                for child in data["children"]:
                    self._populate_tree(item, child)
        except Exception as e:
            logger.error(f"Error populating tree item: {str(e)}")

    def apply_theme(self) -> None:
        try:
            self.theme_manager.apply_theme(self)
        except Exception as e:
            logger.error(f"Error applying theme: {str(e)}")
