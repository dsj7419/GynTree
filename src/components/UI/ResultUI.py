import csv
import logging
import os
import shutil
import tempfile
import time
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QFont, QIcon, QResizeEvent
from PyQt5.QtWidgets import (
    QApplication,
    QDesktopWidget,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from utilities.resource_path import get_resource_path
from utilities.theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class ResultUI(QMainWindow):
    resultUpdated = pyqtSignal()
    clipboardCopyComplete = pyqtSignal()
    saveComplete = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self, controller: Any, theme_manager: ThemeManager, directory_analyzer: Any
    ) -> None:
        super().__init__()
        self.controller = controller
        self.theme_manager = theme_manager
        self.directory_analyzer = directory_analyzer
        self.result_data: Optional[List[Dict[str, str]]] = None
        self._max_retries = 3
        self._retry_delay = 0.5
        self._temp_files: List[str] = []
        self.result_table: Optional[QTableWidget] = None
        self.init_ui()
        self.theme_manager.themeChanged.connect(self.apply_theme)

    def __del__(self) -> None:
        self._cleanup_temp_files()

    def _cleanup_temp_files(self) -> None:
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.error(f"Failed to cleanup temporary file {temp_file}: {str(e)}")
        self._temp_files.clear()

    def init_ui(self) -> None:
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

    def create_styled_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 14))
        return btn

    def update_result(self) -> None:
        if not self.result_table:
            return

        try:
            self.result_data = self.directory_analyzer.get_flat_structure()
            if not self.result_data:
                self.result_table.setRowCount(0)
                return

            self.result_table.setRowCount(len(self.result_data))

            max_path_width = 0
            for row, item_data in enumerate(self.result_data):
                path_item = QTableWidgetItem(item_data["path"])
                desc_item = QTableWidgetItem(item_data["description"])
                self.result_table.setItem(row, 0, path_item)
                self.result_table.setItem(row, 1, desc_item)
                max_path_width = max(
                    max_path_width,
                    self.result_table.fontMetrics().width(item_data["path"]),
                )

            padding = 50
            self.result_table.setColumnWidth(0, max_path_width + padding)
            self.result_table.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.Stretch
            )
            self.result_table.resizeRowsToContents()

            QTimer.singleShot(0, self.adjust_column_widths)

            self.resultUpdated.emit()

        except Exception as e:
            logger.error(f"Error updating results: {str(e)}")
            self.error.emit(f"Failed to update results: {str(e)}")

    def adjust_column_widths(self) -> None:
        if not self.result_table:
            return

        try:
            total_width = self.result_table.viewport().width()
            path_column_width = self.result_table.columnWidth(0)
            description_column_width = total_width - path_column_width
            self.result_table.setColumnWidth(1, description_column_width)
        except Exception as e:
            logger.error(f"Error adjusting column widths: {str(e)}")
            self.error.emit(f"Failed to adjust columns: {str(e)}")

    def copy_to_clipboard(self) -> None:
        if not self.result_table:
            return

        try:
            clipboard_text = "Path,Description\n"
            for row in range(self.result_table.rowCount()):
                row_texts = []
                for col in range(self.result_table.columnCount()):
                    item = self.result_table.item(row, col)
                    row_texts.append(item.text() if item else "")
                clipboard_text += ",".join(row_texts) + "\n"
            QApplication.clipboard().setText(clipboard_text)
            self.clipboardCopyComplete.emit()
        except Exception as e:
            logger.error(f"Error copying to clipboard: {str(e)}")
            self.error.emit(f"Failed to copy to clipboard: {str(e)}")

    def _get_save_file_name(self, file_type: str) -> str:
        if file_type == "txt":
            return QFileDialog.getSaveFileName(
                self, "Save TXT", "", "Text Files (*.txt)"
            )[0]
        elif file_type == "csv":
            return QFileDialog.getSaveFileName(
                self, "Save CSV", "", "CSV Files (*.csv)"
            )[0]
        return ""

    def _create_temp_file(self, file_type: str) -> str:
        temp_suffix = os.urandom(6).hex()
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=f"_{temp_suffix}.{file_type}",
            encoding="utf-8",
            newline="",
        )
        self._temp_files.append(temp_file.name)
        return temp_file.name

    def _write_txt_content(self, file_path: str) -> None:
        if not self.result_data:
            return
        with open(file_path, "w", encoding="utf-8", newline="") as file:
            for item in self.result_data:
                file.write(f"{item['path']}: {item['description']}\n")

    def _write_csv_content(self, file_path: str) -> None:
        if not self.result_data:
            return
        with open(file_path, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Path", "Description"])
            for item in self.result_data:
                writer.writerow([item["path"], item["description"]])

    def _write_temp_file(self, temp_path: str, file_type: str) -> None:
        if file_type == "txt":
            self._write_txt_content(temp_path)
        elif file_type == "csv":
            self._write_csv_content(temp_path)

    def _copy_file_with_retries(self, temp_path: str, final_path: str) -> bool:
        for attempt in range(self._max_retries):
            try:
                target_dir = os.path.dirname(final_path)
                if target_dir:
                    os.makedirs(target_dir, exist_ok=True)

                if os.path.exists(final_path):
                    os.remove(final_path)

                shutil.copy2(temp_path, final_path)

                if temp_path in self._temp_files:
                    self._temp_files.remove(temp_path)

                self.saveComplete.emit()
                return True

            except Exception as e:
                if attempt < self._max_retries - 1:
                    logger.warning(f"Retry {attempt + 1} failed: {str(e)}")
                    time.sleep(self._retry_delay)
                else:
                    logger.error(
                        f"Failed to save file after {self._max_retries} attempts: {e}"
                    )
                    self.error.emit(f"Failed to save file: {str(e)}")
        return False

    def save_file(self, file_type: str) -> None:
        if not self.result_data:
            logger.warning("No data to save")
            return

        try:
            file_name = self._get_save_file_name(file_type)
            if not file_name:
                return

            temp_file_path = self._create_temp_file(file_type)

            try:
                self._write_temp_file(temp_file_path, file_type)
                self._copy_file_with_retries(temp_file_path, file_name)
            except Exception as e:
                logger.error(f"Error writing file: {str(e)}")
                self.error.emit(f"Failed to write file: {str(e)}")

        except Exception as e:
            logger.error(f"Error in save operation: {str(e)}")
            self.error.emit(f"Failed to save: {str(e)}")
        finally:
            self._cleanup_temp_files()

    def resizeEvent(self, event: QResizeEvent) -> None:
        try:
            super().resizeEvent(event)
            self.adjust_column_widths()
        except Exception as e:
            logger.error(f"Error handling resize: {str(e)}")
            self.error.emit(f"Failed to handle resize: {str(e)}")

    def refresh_display(self) -> None:
        self.update_result()

    def apply_theme(self) -> None:
        try:
            self.theme_manager.apply_theme(self)
        except Exception as e:
            logger.error(f"Error applying theme: {str(e)}")
            self.error.emit(f"Failed to apply theme: {str(e)}")

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            self._cleanup_temp_files()
            super().closeEvent(event)
        except Exception as e:
            logger.error(f"Error handling close event: {str(e)}")
