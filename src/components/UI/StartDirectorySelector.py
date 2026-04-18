from typing import Callable

from PyQt5.QtWidgets import QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget


class StartDirectorySelector(QWidget):
    def __init__(self, callback: Callable[[str], None]) -> None:
        super().__init__()
        self.callback = callback
        self.select_button: QPushButton
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select Start Directory"))
        self.select_button = QPushButton("Select Directory")
        self.select_button.clicked.connect(self.select_directory)
        layout.addWidget(self.select_button)
        self.setLayout(layout)
        self.setWindowTitle("Start Directory Selector")

    def select_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Start Directory")
        if directory:
            self.callback(directory)
            self.close()
