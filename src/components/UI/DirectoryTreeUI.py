from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTreeWidget, QPushButton,
                            QHBoxLayout, QTreeWidgetItem, QHeaderView, QMessageBox)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QSize, pyqtSlot
from components.TreeExporter import TreeExporter
from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager
import logging

logger = logging.getLogger(__name__)

class DirectoryTreeUI(QWidget):
    def __init__(self, controller, theme_manager: ThemeManager):
        super().__init__()
        self.controller = controller
        self.theme_manager = theme_manager
        self.directory_structure = None
        self.folder_icon = None
        self.file_icon = None
        self.tree_widget = None
        self.tree_exporter = None
        self._load_icons()
        self.init_ui()
        self.theme_manager.themeChanged.connect(self.apply_theme)

    def _load_icons(self):
        """Safely load icons with error handling"""
        try:
            self.folder_icon = QIcon(get_resource_path("assets/images/folder_icon.png"))
            self.file_icon = QIcon(get_resource_path("assets/images/file_icon.png"))
        except Exception as e:
            logger.error(f"Failed to load icons: {str(e)}")
            self.folder_icon = QIcon()
            self.file_icon = QIcon()

    def init_ui(self):
        """Initialize the user interface with proper error handling"""
        try:
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(30, 30, 30, 30)
            main_layout.setSpacing(20)

            # Header section
            header_layout = self._create_header_layout()
            main_layout.addLayout(header_layout)

            # Tree widget section
            self._setup_tree_widget()
            main_layout.addWidget(self.tree_widget)

            # Export functionality
            self._setup_exporter()

            self.setLayout(main_layout)
            self.setWindowTitle('Directory Tree')
            self.setGeometry(300, 150, 800, 600)
            self.apply_theme()

        except Exception as e:
            logger.error(f"Failed to initialize UI: {str(e)}")
            QMessageBox.critical(self, "Error", "Failed to initialize UI components")

    def _create_header_layout(self):
        """Create and return the header layout with buttons"""
        header_layout = QHBoxLayout()
        
        title_label = QLabel('Directory Tree', font=QFont('Arial', 24, QFont.Bold))
        header_layout.addWidget(title_label)

        # Create buttons
        buttons = {
            'Collapse All': self._handle_collapse_all,
            'Expand All': self._handle_expand_all,
            'Export PNG': self._handle_export_png,
            'Export ASCII': self._handle_export_ascii
        }

        for text, handler in buttons.items():
            btn = self.create_styled_button(text)
            btn.clicked.connect(handler)
            header_layout.addWidget(btn)

        header_layout.setAlignment(Qt.AlignCenter)
        return header_layout

    def _setup_tree_widget(self):
        """Set up the tree widget with proper configuration"""
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(['Name'])
        self.tree_widget.setColumnWidth(0, 300)
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setIconSize(QSize(20, 20))
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)

    def _setup_exporter(self):
        """Initialize the tree exporter with error handling"""
        try:
            self.tree_exporter = TreeExporter(self.tree_widget)
        except Exception as e:
            logger.error(f"Failed to initialize TreeExporter: {str(e)}")
            self.tree_exporter = None
            QMessageBox.warning(self, "Warning", "Export functionality unavailable")

    @pyqtSlot()
    def _handle_collapse_all(self):
        """Handle collapse all button click"""
        try:
            self.tree_widget.collapseAll()
        except Exception as e:
            logger.error(f"Error during collapse all: {str(e)}")

    @pyqtSlot()
    def _handle_expand_all(self):
        """Handle expand all button click"""
        try:
            self.tree_widget.expandAll()
        except Exception as e:
            logger.error(f"Error during expand all: {str(e)}")

    @pyqtSlot()
    def _handle_export_png(self):
        """Handle PNG export with error handling"""
        try:
            if self.tree_exporter:
                self.tree_exporter.export_as_image()
        except Exception as e:
            logger.error(f"Error during PNG export: {str(e)}")
            QMessageBox.warning(self, "Export Error", "Failed to export as PNG")

    @pyqtSlot()
    def _handle_export_ascii(self):
        """Handle ASCII export with error handling"""
        try:
            if self.tree_exporter:
                self.tree_exporter.export_as_ascii()
        except Exception as e:
            logger.error(f"Error during ASCII export: {str(e)}")
            QMessageBox.warning(self, "Export Error", "Failed to export as ASCII")

    def create_styled_button(self, text):
        """Create a styled button with error handling"""
        btn = QPushButton(text)
        btn.setFont(QFont('Arial', 14))
        return btn

    def update_tree(self, directory_structure):
        """Update the tree with proper error handling"""
        try:
            self.directory_structure = directory_structure
            self.tree_widget.clear()
            if directory_structure:
                self._populate_tree(self.tree_widget.invisibleRootItem(), self.directory_structure)
                self.tree_widget.expandAll()
        except Exception as e:
            logger.error(f"Error updating tree: {str(e)}")
            QMessageBox.warning(self, "Update Error", "Failed to update directory tree")

    def _populate_tree(self, parent, data):
        """Populate tree with proper error handling"""
        try:
            item = QTreeWidgetItem(parent)
            item.setText(0, data['name'])
            
            # Set icon based on type with null check
            icon = self.folder_icon if data['type'] == 'directory' else self.file_icon
            if not icon.isNull():
                item.setIcon(0, icon)

            if 'children' in data and isinstance(data['children'], list):
                for child in data['children']:
                    self._populate_tree(item, child)
        except Exception as e:
            logger.error(f"Error populating tree item: {str(e)}")

    def apply_theme(self):
        """Apply theme with error handling"""
        try:
            self.theme_manager.apply_theme(self)
        except Exception as e:
            logger.error(f"Error applying theme: {str(e)}")