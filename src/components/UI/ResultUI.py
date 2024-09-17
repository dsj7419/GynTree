# GynTree: This file defines the ResultUI class, which displays the analysis results in a user-friendly format and provides options to view, copy, and save the results in different formats.

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QLabel, QPushButton,
                             QFileDialog, QWidget, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from utilities.Utilities import copy_to_clipboard
import json

class ResultUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.result_data = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Analysis Results')
        self.setWindowIcon(QIcon('assets/images/GynTree_logo 64X64.ico'))
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 18px;
                color: #333;
                margin-bottom: 10px;
            }
            QTableWidget {
                font-size: 14px;
                border: 1px solid #ddd;
                border-radius: 4px;
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
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel('Directory Analysis Results')
        title.setFont(QFont('Arial', 20, QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # Result table
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(['File', 'Description'])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setWordWrap(True)
        self.result_table.verticalHeader().setDefaultSectionSize(60)
        layout.addWidget(self.result_table)

        # Button layout
        button_layout = QHBoxLayout()

        copy_button = QPushButton('Copy to Clipboard')
        copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_button)

        save_csv_button = QPushButton('Save as CSV')
        save_csv_button.clicked.connect(lambda: self.save_file('csv'))
        button_layout.addWidget(save_csv_button)

        save_txt_button = QPushButton('Save as TXT')
        save_txt_button.clicked.connect(lambda: self.save_file('txt'))
        button_layout.addWidget(save_txt_button)

        layout.addLayout(button_layout)

        self.setGeometry(300, 300, 800, 600)

    def update_result(self, result):
        """
        Update the result table with the analysis data.
        Accepts a result dictionary and populates the table.
        """
        self.result_data = result if isinstance(result, dict) else json.loads(result)
        self.result_table.setRowCount(len(self.result_data))
        
        for row, (file_path, description) in enumerate(self.result_data.items()):
            # File path column
            file_item = QTableWidgetItem(file_path.replace('\\', '/'))
            file_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.result_table.setItem(row, 0, file_item)
            
            # Description column
            desc_item = QTableWidgetItem(description)
            desc_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.result_table.setItem(row, 1, desc_item)
        
        # Adjust row sizes to fit the content
        self.result_table.resizeRowsToContents()

    def copy_to_clipboard(self):
        """
        Copy the result data to the clipboard in a readable format.
        """
        clipboard_text = "\n".join([f"{file}: {desc}" for file, desc in self.result_data.items()])
        copy_to_clipboard(clipboard_text)

    def save_file(self, file_type):
        """
        Save the analysis result to a file.
        Supports CSV and TXT formats based on the file_type argument.
        """
        options = QFileDialog.Options()
        file_name = None
        if file_type == 'csv':
            file_name, _ = QFileDialog.getSaveFileName(self, 'Save CSV', '', 'CSV Files (*.csv)', options=options)
        elif file_type == 'txt':
            file_name, _ = QFileDialog.getSaveFileName(self, 'Save TXT', '', 'Text Files (*.txt)', options=options)

        if file_name:
            self._write_file(file_name, file_type)

    def _write_file(self, file_name, file_type):
        """
        Helper function to write result data to a file.
        Ensures proper formatting based on the file_type (CSV or TXT).
        """
        with open(file_name, 'w', encoding='utf-8') as file:
            if file_type == 'csv':
                file.write("File,Description\n")
                for file_path, description in self.result_data.items():
                    # Ensure proper CSV formatting with escaping double quotes
                    escaped_description = description.replace('"', '""')
                    file.write(f'"{file_path}","{escaped_description}"\n')
            elif file_type == 'txt':
                for file_path, description in self.result_data.items():
                    # Plain text formatting for the TXT output
                    file.write(f"{file_path}: {description}\n")
