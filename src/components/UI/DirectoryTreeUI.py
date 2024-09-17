from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTreeWidget, QPushButton, QHBoxLayout)
from PyQt5.QtGui import QFont, QIcon
from components.TreeStructureManager import TreeStructureManager
from components.TreeExporter import TreeExporter

class DirectoryTreeUI(QWidget):
    def __init__(self, directory_analyzer):
        super().__init__()
        self.directory_analyzer = directory_analyzer
        self.folder_icon = QIcon("assets/images/GynTree_logo 64X64.ico")
        self.file_icon = QIcon("assets/images/GynTree_logo.png")
        self.tree_widget = None
        self.tree_structure_manager = TreeStructureManager(self.directory_analyzer, self.folder_icon, self.file_icon)
        self.tree_exporter = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header with title and buttons
        header_layout = QHBoxLayout()
        title_label = QLabel('Directory Tree', font=QFont('Arial', 14, QFont.Bold))
        header_layout.addWidget(title_label)

        # Expand/Collapse buttons
        expand_btn = QPushButton('Expand All')
        collapse_btn = QPushButton('Collapse All')
        header_layout.addWidget(expand_btn)
        header_layout.addWidget(collapse_btn)

        # Export buttons
        export_png_btn = QPushButton('Export as PNG')
        export_ascii_btn = QPushButton('Export as ASCII')
        header_layout.addWidget(export_png_btn)
        header_layout.addWidget(export_ascii_btn)

        layout.addLayout(header_layout)

        # Set up the tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(['Name', 'Type'])
        self.tree_widget.setAlternatingRowColors(True)
        layout.addWidget(self.tree_widget)

        self.tree_structure_manager.populate_tree(self.tree_widget)
        self.tree_exporter = TreeExporter(self.tree_widget)

        # Button connections
        expand_btn.clicked.connect(self.tree_widget.expandAll)
        collapse_btn.clicked.connect(self.tree_widget.collapseAll)
        export_png_btn.clicked.connect(self.tree_exporter.export_as_image)
        export_ascii_btn.clicked.connect(self.tree_exporter.export_as_ascii)

        self.setLayout(layout)
        self.setWindowTitle('Directory Tree')
        self.resize(800, 600)
