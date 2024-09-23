from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTreeWidget, QPushButton,
                             QHBoxLayout, QTreeWidgetItem, QHeaderView)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QSize
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
        self.folder_icon = QIcon(get_resource_path("assets/images/folder_icon.png"))
        self.file_icon = QIcon(get_resource_path("assets/images/file_icon.png"))
        self.tree_widget = None
        self.tree_exporter = None
        self.init_ui()

        self.theme_manager.themeChanged.connect(self.apply_theme)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title_label = QLabel('Directory Tree', font=QFont('Arial', 24, QFont.Bold))
        header_layout.addWidget(title_label)

        collapse_btn = self.create_styled_button('Collapse All')
        expand_btn = self.create_styled_button('Expand All')
        export_png_btn = self.create_styled_button('Export PNG')
        export_ascii_btn = self.create_styled_button('Export ASCII')

        header_layout.addWidget(collapse_btn)
        header_layout.addWidget(expand_btn)
        header_layout.addWidget(export_png_btn)
        header_layout.addWidget(export_ascii_btn)
        header_layout.setAlignment(Qt.AlignCenter)
        main_layout.addLayout(header_layout)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(['Name'])
        self.tree_widget.setColumnWidth(0, 300)
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setIconSize(QSize(20, 20))
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        main_layout.addWidget(self.tree_widget)

        self.tree_exporter = TreeExporter(self.tree_widget)

        collapse_btn.clicked.connect(self.tree_widget.collapseAll)
        expand_btn.clicked.connect(self.tree_widget.expandAll)
        export_png_btn.clicked.connect(self.tree_exporter.export_as_image)
        export_ascii_btn.clicked.connect(self.tree_exporter.export_as_ascii)

        self.setLayout(main_layout)
        self.setWindowTitle('Directory Tree')
        self.setGeometry(300, 150, 800, 600)

        self.apply_theme()

    def create_styled_button(self, text):
        btn = QPushButton(text)
        btn.setFont(QFont('Arial', 14))
        return btn

    def update_tree(self, directory_structure):
        self.directory_structure = directory_structure
        self.tree_widget.clear()
        self._populate_tree(self.tree_widget.invisibleRootItem(), self.directory_structure)
        self.tree_widget.expandAll()

    def _populate_tree(self, parent, data):
        item = QTreeWidgetItem(parent)
        item.setText(0, data['name'])
        item.setIcon(0, self.folder_icon if data['type'] == 'directory' else self.file_icon)
        if 'children' in data:
            for child in data['children']:
                self._populate_tree(item, child)

    def apply_theme(self):
        self.theme_manager.apply_theme(self)