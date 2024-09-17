from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, 
                             QHBoxLayout, QFileDialog, QFrame, QSplitter)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
import os

class ExclusionsManager(QWidget):
    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        # Use existing methods to get excluded directories and files
        self.excluded_dirs = settings_manager.get_excluded_dirs()
        self.excluded_files = settings_manager.get_excluded_files()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Exclusions Manager')
        self.setWindowIcon(QIcon('assets/images/GynTree_logo 64X64.ico'))
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
            QListWidget {
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

        # Excluded directories
        dir_frame = QFrame()
        dir_layout = QVBoxLayout(dir_frame)
        dir_layout.addWidget(QLabel('Excluded Directories'))
        self.dir_list = QListWidget()
        self.dir_list.addItems(self.excluded_dirs)
        dir_layout.addWidget(self.dir_list)

        dir_buttons_layout = QHBoxLayout()
        add_dir_button = QPushButton('Add Directory')
        remove_dir_button = QPushButton('Remove Directory')
        add_dir_button.clicked.connect(self.add_directory)
        remove_dir_button.clicked.connect(self.remove_directory)
        dir_buttons_layout.addWidget(add_dir_button)
        dir_buttons_layout.addWidget(remove_dir_button)

        dir_layout.addLayout(dir_buttons_layout)
        splitter.addWidget(dir_frame)

        # Excluded files
        file_frame = QFrame()
        file_layout = QVBoxLayout(file_frame)
        file_layout.addWidget(QLabel('Excluded Files'))
        self.file_list = QListWidget()
        self.file_list.addItems(self.excluded_files)
        file_layout.addWidget(self.file_list)

        file_buttons_layout = QHBoxLayout()
        add_file_button = QPushButton('Add File')
        remove_file_button = QPushButton('Remove File')
        add_file_button.clicked.connect(self.add_file)
        remove_file_button.clicked.connect(self.remove_file)
        file_buttons_layout.addWidget(add_file_button)
        file_buttons_layout.addWidget(remove_file_button)

        file_layout.addLayout(file_buttons_layout)
        splitter.addWidget(file_frame)

        layout.addWidget(splitter)

        save_button = QPushButton('Save & Exit')
        save_button.clicked.connect(self.save_and_exit)
        layout.addWidget(save_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setGeometry(400, 300, 800, 600)

    def add_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select directory to exclude')
        if directory and directory not in self.excluded_dirs:
            self.excluded_dirs.append(directory)
            self.dir_list.addItem(directory)

    def remove_directory(self):
        selected_items = self.dir_list.selectedItems()
        if selected_items:
            for item in selected_items:
                self.excluded_dirs.remove(item.text())
                self.dir_list.takeItem(self.dir_list.row(item))

    def add_file(self):
        file, _ = QFileDialog.getOpenFileName(self, 'Select file to exclude')
        if file and file not in self.excluded_files:
            self.excluded_files.append(file)
            self.file_list.addItem(file)

    def remove_file(self):
        selected_items = self.file_list.selectedItems()
        if selected_items:
            for item in selected_items:
                self.excluded_files.remove(item.text())
                self.file_list.takeItem(self.file_list.row(item))

    def save_and_exit(self):
        # Save updated exclusions to settings
        self.settings_manager.update_settings({
            'excluded_dirs': self.excluded_dirs,
            'excluded_files': self.excluded_files
        })
        self.close()
