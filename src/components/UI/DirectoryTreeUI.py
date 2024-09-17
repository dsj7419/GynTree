"""
GynTree: This module implements the DirectoryTreeUI class for visualizing directory structures.
It creates an interactive tree view of the analyzed directory, allowing users to
explore the structure visually. The class also provides options for collapsing/expanding
nodes and exporting the tree view in different formats.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTreeWidget, QPushButton, QHBoxLayout, QTreeWidgetItem, QHeaderView)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QSize
from components.TreeExporter import TreeExporter
from utilities.resource_path import get_resource_path

class DirectoryTreeUI(QWidget):
    def __init__(self, directory_structure):
        super().__init__()
        self.directory_structure = directory_structure
        self.folder_icon = QIcon(get_resource_path("assets/images/folder_icon.png"))
        self.file_icon = QIcon(get_resource_path("assets/images/file_icon.png"))
        self.tree_widget = None
        self.tree_exporter = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        title_label = QLabel('Directory Tree', font=QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(title_label)

        collapse_btn = QPushButton('Collapse All')
        header_layout.addWidget(collapse_btn)

        export_png_btn = QPushButton('Export as PNG')
        export_ascii_btn = QPushButton('Export as ASCII')
        header_layout.addWidget(export_png_btn)
        header_layout.addWidget(export_ascii_btn)

        layout.addLayout(header_layout)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(['Name'])
        self.tree_widget.setColumnWidth(0, 300)
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setIconSize(QSize(20, 20))
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        layout.addWidget(self.tree_widget)

        self._populate_tree(self.tree_widget.invisibleRootItem(), self.directory_structure)
        self.tree_widget.expandAll()
        self.tree_exporter = TreeExporter(self.tree_widget)

        collapse_btn.clicked.connect(self.tree_widget.collapseAll)
        export_png_btn.clicked.connect(self.tree_exporter.export_as_image)
        export_ascii_btn.clicked.connect(self.tree_exporter.export_as_ascii)

        self.setLayout(layout)
        self.setWindowTitle('Directory Tree')
        self.resize(800, 600)

    def _populate_tree(self, parent, data):
        item = QTreeWidgetItem(parent)
        item.setText(0, data['name'])
        item.setIcon(0, self.folder_icon if data['type'] == 'Directory' else self.file_icon)
        
        if 'children' in data:
            for child in data['children']:
                self._populate_tree(item, child)