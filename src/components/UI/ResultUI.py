"""
GynTree: This module defines the ResultUI class, which displays the directory analysis results.
It provides a user-friendly interface for viewing, copying, and exporting analysis data.
The ResultUI class handles the presentation of analysis results in a tabular format,
offering features like adjustable columns and various export options.
"""

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QLabel, QPushButton,
                             QFileDialog, QWidget, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QApplication, QSplitter,
                             QDesktopWidget)
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer
import csv
from utilities.resource_path import get_resource_path

class ResultUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.result_data = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Analysis Results')
        self.setWindowIcon(QIcon(get_resource_path('assets/images/GynTree_logo 64X64.ico')))
        
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.WindowText, QColor(50, 50, 50))
        palette.setColor(QPalette.Button, QColor(220, 220, 220))
        palette.setColor(QPalette.ButtonText, QColor(50, 50, 50))
        self.setPalette(palette)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel('Directory Analysis Results')
        title.setFont(QFont('Arial', 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setMaximumHeight(40)
        layout.addWidget(title)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(['Path', 'Description'])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setWordWrap(True)
        self.result_table.setTextElideMode(Qt.ElideNone)
        self.result_table.setShowGrid(True)
        self.result_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d6d9dc;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: 1px solid #d6d9dc;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.result_table)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        copy_button = QPushButton('Copy to Clipboard')
        copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_button)

        save_txt_button = QPushButton('Save as TXT')
        save_txt_button.clicked.connect(lambda: self.save_file('txt'))
        button_layout.addWidget(save_txt_button)

        save_csv_button = QPushButton('Save as CSV')
        save_csv_button.clicked.connect(lambda: self.save_file('csv'))
        button_layout.addWidget(save_csv_button)

        layout.addLayout(button_layout)

        screen = QDesktopWidget().screenGeometry()
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.8)
        self.setGeometry(int(screen.width() * 0.1), int(screen.height() * 0.1), width, height)

    def update_result(self, result):
        self.result_data = result
        self.result_table.setRowCount(len(result))
        max_path_width = 0
        for row, item in enumerate(result):
            path_item = QTableWidgetItem(item['path'])
            self.result_table.setItem(row, 0, path_item)
            self.result_table.setItem(row, 1, QTableWidgetItem(item['description']))
            max_path_width = max(max_path_width, self.result_table.fontMetrics().width(item['path']))

        padding = 50
        self.result_table.setColumnWidth(0, max_path_width + padding)
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        self.result_table.resizeRowsToContents()

        QTimer.singleShot(0, self.adjust_column_widths)

    def adjust_column_widths(self):
        total_width = self.result_table.viewport().width()
        path_column_width = self.result_table.columnWidth(0)
        description_column_width = total_width - path_column_width
        self.result_table.setColumnWidth(1, description_column_width)

    def copy_to_clipboard(self):
        clipboard_text = "Path,Description\n"
        for row in range(self.result_table.rowCount()):
            row_data = [
                self.result_table.item(row, col).text()
                for col in range(self.result_table.columnCount())
            ]
            clipboard_text += ",".join(row_data) + "\n"
        QApplication.clipboard().setText(clipboard_text)

    def save_file(self, file_type):
        options = QFileDialog.Options()
        if file_type == 'txt':
            file_name, _ = QFileDialog.getSaveFileName(self, "Save TXT", "", "Text Files (*.txt)", options=options)
        elif file_type == 'csv':
            file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)", options=options)
        else:
            return

        if file_name:
            with open(file_name, 'w', newline='', encoding='utf-8') as file:
                if file_type == 'txt':
                    for item in self.result_data:
                        file.write(f"{item['path']}: {item['description']}\n")
                elif file_type == 'csv':
                    writer = csv.writer(file)
                    writer.writerow(['Path', 'Description'])
                    for item in self.result_data:
                        writer.writerow([item['path'], item['description']])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_column_widths()