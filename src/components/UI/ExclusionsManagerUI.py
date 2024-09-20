from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout,
    QFileDialog, QMessageBox, QGroupBox, QHeaderView, QSplitter
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from services.SettingsManager import SettingsManager
from utilities.resource_path import get_resource_path
import os

class ExclusionsManagerUI(QWidget):
    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        self.settings_manager = settings_manager
        self.setWindowTitle('Exclusions Manager')
        self.setWindowIcon(QIcon(get_resource_path('assets/images/gyntree_logo 64x64.ico')))
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: #333;
            }
            QLabel {
                font-size: 18px;
                color: #333;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel('Manage Exclusions')
        title.setFont(QFont('Arial', 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Splitter for Root Exclusions and Detailed Exclusions
        splitter = QSplitter(Qt.Vertical)

        # Root Exclusions (Read-Only)
        root_group = QGroupBox("Root Exclusions (Non-Editable)")
        root_layout = QVBoxLayout()
        root_tree = QTreeWidget()
        root_tree.setHeaderLabels(["Excluded Paths"])
        root_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        root_exclusions = self.settings_manager.get_root_exclusions()
        self.populate_root_exclusions(root_tree, root_exclusions)
        root_layout.addWidget(root_tree)
        root_group.setLayout(root_layout)
        splitter.addWidget(root_group)

        # Detailed Exclusions (Editable)
        detailed_group = QGroupBox("Detailed Exclusions")
        detailed_layout = QVBoxLayout()
        self.exclusion_tree = QTreeWidget()
        self.exclusion_tree.setHeaderLabels(['Type', 'Path'])
        self.exclusion_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.exclusion_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        detailed_layout.addWidget(self.exclusion_tree)
        detailed_group.setLayout(detailed_layout)
        splitter.addWidget(detailed_group)

        layout.addWidget(splitter)

        buttons_layout = QHBoxLayout()
        add_dir_button = QPushButton('Add Directory')
        add_file_button = QPushButton('Add File')
        remove_button = QPushButton('Remove Selected')
        buttons_layout.addWidget(add_dir_button)
        buttons_layout.addWidget(add_file_button)
        buttons_layout.addWidget(remove_button)
        layout.addLayout(buttons_layout)

        save_button = QPushButton('Save & Exit')
        save_button.clicked.connect(self.save_and_exit)
        layout.addWidget(save_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setGeometry(400, 300, 800, 600)

        add_dir_button.clicked.connect(self.add_directory)
        add_file_button.clicked.connect(self.add_file)
        remove_button.clicked.connect(self.remove_selected)

        self.populate_exclusion_tree()

    def populate_root_exclusions(self, tree, exclusions):
        for path in sorted(exclusions):
            item = QTreeWidgetItem(tree, [path])
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
        tree.expandAll()

    def populate_exclusion_tree(self):
        self.exclusion_tree.clear()
        exclusions = self.settings_manager.get_all_exclusions()

        dirs_item = QTreeWidgetItem(self.exclusion_tree, ['excluded_dirs'])
        dirs_item.setFlags(dirs_item.flags() & ~Qt.ItemIsSelectable)
        for directory in sorted(exclusions.get('excluded_dirs', [])):
            item = QTreeWidgetItem(dirs_item, ['Directory', directory])
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEditable)

        files_item = QTreeWidgetItem(self.exclusion_tree, ['excluded_files'])
        files_item.setFlags(files_item.flags() & ~Qt.ItemIsSelectable)
        for file in sorted(exclusions.get('excluded_files', [])):
            item = QTreeWidgetItem(files_item, ['File', file])
            item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEditable)

        self.exclusion_tree.expandAll()

    def add_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory to Exclude')
        if directory:
            relative_directory = os.path.relpath(directory, self.settings_manager.project.start_directory)
            exclusions = self.settings_manager.get_all_exclusions()
            if relative_directory in exclusions['excluded_dirs'] or relative_directory in exclusions['root_exclusions']:
                QMessageBox.warning(self, "Duplicate Entry", f"The directory '{relative_directory}' is already excluded.")
                return
            exclusions['excluded_dirs'].add(relative_directory)
            self.settings_manager.update_settings({'excluded_dirs': list(exclusions['excluded_dirs'])})
            self.populate_exclusion_tree()

    def add_file(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Select File to Exclude')
        if file:
            relative_file = os.path.relpath(file, self.settings_manager.project.start_directory)
            exclusions = self.settings_manager.get_all_exclusions()
            if relative_file in exclusions['excluded_files'] or any(relative_file.startswith(root_dir) for root_dir in exclusions['root_exclusions']):
                QMessageBox.warning(self, "Duplicate Entry", f"The file '{relative_file}' is already excluded or within a root exclusion.")
                return
            exclusions['excluded_files'].add(relative_file)
            self.settings_manager.update_settings({'excluded_files': list(exclusions['excluded_files'])})
            self.populate_exclusion_tree()

    def remove_selected(self):
        selected_items = self.exclusion_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select an exclusion to remove.")
            return
        for item in selected_items:
            parent = item.parent()
            if parent:
                path = item.text(1)
                category = parent.text(0)
                exclusions = self.settings_manager.get_all_exclusions()
                if category == 'excluded_dirs':
                    exclusions['excluded_dirs'].discard(path)
                elif category == 'excluded_files':
                    exclusions['excluded_files'].discard(path)
                self.settings_manager.update_settings({
                    'excluded_dirs': list(exclusions['excluded_dirs']),
                    'excluded_files': list(exclusions['excluded_files'])
                })
        self.populate_exclusion_tree()

    def save_and_exit(self):
        self.settings_manager.save_settings()
        QMessageBox.information(self, "Exclusions Saved", "Exclusions have been successfully saved.")
        self.close()

    def closeEvent(self, event):
        super().closeEvent(event)