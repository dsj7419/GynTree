# GynTree: Implements a UI component for selecting the starting directory for analysis.

from PyQt5.QtWidgets import QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget


class StartDirectorySelector(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select Start Directory"))
        self.select_button = QPushButton("Select Directory")
        self.select_button.clicked.connect(self.select_directory)
        layout.addWidget(self.select_button)

        self.setLayout(layout)
        self.setWindowTitle("Start Directory Selector")

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Start Directory")
        if directory:
            self.callback(directory)
            self.close()
