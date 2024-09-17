# GynTree: Provides a UI for managing user-defined file and directory exclusions.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QPushButton, 
                             QHBoxLayout, QFileDialog, QFrame, QSplitter, QTextEdit)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from services.ExclusionManagerService import ExclusionManagerService
from utilities.resource_path import get_resource_path

class ExclusionsManager(QWidget):
    def __init__(self, settings_manager):
        super().__init__()
        self.exclusion_manager_service = ExclusionManagerService(settings_manager)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Exclusions Manager')
        self.setWindowIcon(QIcon(get_resource_path('assets/images/GynTree_logo 64X64.ico')))
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: #333;
            }
            QLabel {
                font-size: 16px;
                color: #333;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel('Manage Exclusions')
        title.setFont(QFont('Arial', 20, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)

        splitter = QSplitter(Qt.Horizontal)

        # Aggregated view
        aggregated_frame = QFrame()
        aggregated_layout = QVBoxLayout(aggregated_frame)
        aggregated_layout.addWidget(QLabel('Aggregated Exclusions'))
        self.aggregated_text = QTextEdit()
        self.aggregated_text.setReadOnly(True)
        aggregated_layout.addWidget(self.aggregated_text)
        splitter.addWidget(aggregated_frame)

        # Detailed view
        detailed_frame = QFrame()
        detailed_layout = QVBoxLayout(detailed_frame)
        detailed_layout.addWidget(QLabel('Detailed Exclusions'))
        self.exclusion_tree = QTreeWidget()
        self.exclusion_tree.setHeaderLabels(['Type', 'Path'])
        detailed_layout.addWidget(self.exclusion_tree)
        splitter.addWidget(detailed_frame)

        layout.addWidget(splitter)

        buttons_layout = QHBoxLayout()
        add_dir_button = QPushButton('Add Directory')
        add_file_button = QPushButton('Add File')
        remove_button = QPushButton('Remove Selected')
        add_dir_button.clicked.connect(self.add_directory)
        add_file_button.clicked.connect(self.add_file)
        remove_button.clicked.connect(self.remove_selected)
        buttons_layout.addWidget(add_dir_button)
        buttons_layout.addWidget(add_file_button)
        buttons_layout.addWidget(remove_button)
        layout.addLayout(buttons_layout)

        save_button = QPushButton('Save & Exit')
        save_button.clicked.connect(self.save_and_exit)
        layout.addWidget(save_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setGeometry(400, 300, 800, 600)

        self.update_exclusions_view()

    def update_exclusions_view(self):
        self.aggregated_text.setText(self.exclusion_manager_service.get_aggregated_exclusions())

        self.exclusion_tree.clear()
        detailed_exclusions = self.exclusion_manager_service.get_detailed_exclusions()
        dir_item = QTreeWidgetItem(self.exclusion_tree, ['Directories'])
        file_item = QTreeWidgetItem(self.exclusion_tree, ['Files'])
        for directory in detailed_exclusions['directories']:
            QTreeWidgetItem(dir_item, ['', directory])
        for file in detailed_exclusions['files']:
            QTreeWidgetItem(file_item, ['', file])
        self.exclusion_tree.expandAll()

    def add_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select directory to exclude')
        if self.exclusion_manager_service.add_directory(directory):
            self.update_exclusions_view()

    def add_file(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Select file to exclude')
        if self.exclusion_manager_service.add_file(file):
            self.update_exclusions_view()

    def remove_selected(self):
        selected_items = self.exclusion_tree.selectedItems()
        for item in selected_items:
            if item.parent():
                path = item.text(1)
                if self.exclusion_manager_service.remove_exclusion(path):
                    self.update_exclusions_view()

    def save_and_exit(self):
        self.exclusion_manager_service.save_exclusions()
        self.close()