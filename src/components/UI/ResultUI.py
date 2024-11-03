import csv
import logging
import os
import shutil
import tempfile
import time

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QDesktopWidget,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class ResultUI(QMainWindow):
    # Define signals for operations
    resultUpdated = pyqtSignal()
    clipboardCopyComplete = pyqtSignal()
    saveComplete = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, controller, theme_manager: ThemeManager, directory_analyzer):
        super().__init__()
        self.controller = controller
        self.theme_manager = theme_manager
        self.directory_analyzer = directory_analyzer
        self.result_data = None
        self._max_retries = 3
        self._retry_delay = 0.5
        self._temp_files = []
        self.init_ui()
        self.theme_manager.themeChanged.connect(self.apply_theme)

    def __del__(self):
        """Cleanup temporary resources upon deletion"""
        self._cleanup_temp_files()

    def _cleanup_temp_files(self):
        """Clean up any temporary files created during export."""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.error(f"Failed to cleanup temporary file {temp_file}: {str(e)}")
        self._temp_files.clear()

    def init_ui(self):
        self.setWindowTitle("Analysis Results")
        self.setWindowIcon(QIcon(get_resource_path("assets/images/GynTree_logo.ico")))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Analysis Results")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setMaximumHeight(40)
        layout.addWidget(title)

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["Path", "Description"])
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setWordWrap(True)
        self.result_table.setTextElideMode(Qt.ElideNone)
        self.result_table.setShowGrid(True)
        layout.addWidget(self.result_table)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        copy_button = self.create_styled_button("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_button)

        save_txt_button = self.create_styled_button("Save as TXT")
        save_txt_button.clicked.connect(lambda: self.save_file("txt"))
        button_layout.addWidget(save_txt_button)

        save_csv_button = self.create_styled_button("Save as CSV")
        save_csv_button.clicked.connect(lambda: self.save_file("csv"))
        button_layout.addWidget(save_csv_button)

        layout.addLayout(button_layout)

        screen = QDesktopWidget().screenGeometry()
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.8)
        self.setGeometry(
            int(screen.width() * 0.1), int(screen.height() * 0.1), width, height
        )

        self.apply_theme()

    def create_styled_button(self, text):
        """Helper method to create styled buttons."""
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 14))
        return btn

    def update_result(self):
        """Updates the result table with data from the directory analyzer."""
        try:
            # Get data from the directory analyzer passed during initialization
            self.result_data = self.directory_analyzer.get_flat_structure()

            # Clear existing table data
            self.result_table.setRowCount(0)

            # Set the row count before populating
            self.result_table.setRowCount(len(self.result_data))

            # Populate table
            max_path_width = 0
            for row, item in enumerate(self.result_data):
                path_item = QTableWidgetItem(item["path"])
                desc_item = QTableWidgetItem(item["description"])
                self.result_table.setItem(row, 0, path_item)
                self.result_table.setItem(row, 1, desc_item)
                max_path_width = max(
                    max_path_width, self.result_table.fontMetrics().width(item["path"])
                )

            padding = 50
            self.result_table.setColumnWidth(0, max_path_width + padding)
            self.result_table.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.Stretch
            )
            self.result_table.resizeRowsToContents()

            # Ensure column widths are properly adjusted
            QTimer.singleShot(0, self.adjust_column_widths)

            # Emit signal after successful update
            self.resultUpdated.emit()

        except Exception as e:
            logger.error(f"Error updating results: {str(e)}")
            self.error.emit(f"Failed to update results: {str(e)}")

    def adjust_column_widths(self):
        """Adjust the widths of the result table columns to fit the available space."""
        try:
            total_width = self.result_table.viewport().width()
            path_column_width = self.result_table.columnWidth(0)
            description_column_width = total_width - path_column_width
            self.result_table.setColumnWidth(1, description_column_width)
        except Exception as e:
            logger.error(f"Error adjusting column widths: {str(e)}")
            self.error.emit(f"Failed to adjust columns: {str(e)}")

    def copy_to_clipboard(self):
        """Copy the result data to the system clipboard."""
        try:
            clipboard_text = "Path,Description\n"
            for row in range(self.result_table.rowCount()):
                row_data = [
                    self.result_table.item(row, col).text()
                    for col in range(self.result_table.columnCount())
                ]
                clipboard_text += ",".join(row_data) + "\n"
            QApplication.clipboard().setText(clipboard_text)
            self.clipboardCopyComplete.emit()
        except Exception as e:
            logger.error(f"Error copying to clipboard: {str(e)}")
            self.error.emit(f"Failed to copy to clipboard: {str(e)}")

    def save_file(self, file_type):
        """Save the result data to a file (TXT or CSV)."""
        try:
            if not self.result_data:
                logger.warning("No data to save")
                return

            if file_type == "txt":
                file_name, _ = QFileDialog.getSaveFileName(
                    self, "Save TXT", "", "Text Files (*.txt)"
                )
            elif file_type == "csv":
                file_name, _ = QFileDialog.getSaveFileName(
                    self, "Save CSV", "", "CSV Files (*.csv)"
                )
            else:
                logger.error(f"Invalid file type: {file_type}")
                return

            if not file_name:
                return

            # Create temporary file
            temp_suffix = os.urandom(6).hex()
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                suffix=f"_{temp_suffix}.{file_type}",
                encoding="utf-8",
                newline="",
            )
            self._temp_files.append(temp_file.name)

            # Write to temporary file
            with open(temp_file.name, "w", encoding="utf-8", newline="") as file:
                if file_type == "txt":
                    for item in self.result_data:
                        file.write(f"{item['path']}: {item['description']}\n")
                elif file_type == "csv":
                    writer = csv.writer(file)
                    writer.writerow(["Path", "Description"])
                    for item in self.result_data:
                        writer.writerow([item["path"], item["description"]])

            # Attempt to move to final location with retries
            for attempt in range(self._max_retries):
                try:
                    # Ensure target directory exists
                    target_dir = os.path.dirname(file_name)
                    if target_dir:
                        os.makedirs(target_dir, exist_ok=True)

                    # If target file exists, try to remove it
                    if os.path.exists(file_name):
                        os.remove(file_name)

                    # Copy the file instead of moving it
                    shutil.copy2(temp_file.name, file_name)

                    # Only remove from tracking if successful
                    if temp_file.name in self._temp_files:
                        self._temp_files.remove(temp_file.name)

                    # Always emit signal on successful save
                    self.saveComplete.emit()
                    return

                except Exception as e:
                    if attempt < self._max_retries - 1:
                        logger.warning(f"Retry {attempt + 1} failed: {str(e)}")
                        time.sleep(self._retry_delay)
                    else:
                        logger.error(f"Failed to save file: {str(e)}")
                        self.error.emit(f"Failed to save file: {str(e)}")

        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            self.error.emit(f"Failed to save file: {str(e)}")
        finally:
            self._cleanup_temp_files()

    def resizeEvent(self, event):
        """Handle window resize events."""
        try:
            super().resizeEvent(event)
            self.adjust_column_widths()
        except Exception as e:
            logger.error(f"Error handling resize: {str(e)}")
            self.error.emit(f"Failed to handle resize: {str(e)}")

    def refresh_display(self):
        """Refresh the display with current data."""
        self.update_result()

    def apply_theme(self):
        """Apply the current theme to the UI."""
        try:
            self.theme_manager.apply_theme(self)
        except Exception as e:
            logger.error(f"Error applying theme: {str(e)}")
            self.error.emit(f"Failed to apply theme: {str(e)}")

    def closeEvent(self, event):
        """Handle window close events."""
        try:
            self._cleanup_temp_files()
            super().closeEvent(event)
        except Exception as e:
            logger.error(f"Error handling close event: {str(e)}")
