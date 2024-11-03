import os

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget

from utilities.resource_path import get_resource_path


class ThemeManager(QObject):
    themeChanged = pyqtSignal(str)
    _instance = None

    @staticmethod
    def getInstance():
        if ThemeManager._instance is None:
            ThemeManager._instance = ThemeManager()
        return ThemeManager._instance

    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.light_theme = self.load_stylesheet("light")
        self.dark_theme = self.load_stylesheet("dark")

    def load_stylesheet(self, theme_name):
        stylesheet_path = get_resource_path(f"styles/{theme_name}_theme.qss")
        if not os.path.exists(stylesheet_path):
            raise FileNotFoundError(f"Stylesheet {stylesheet_path} not found")
        with open(stylesheet_path, "r") as f:
            return f.read()

    def get_current_theme(self):
        return self.current_theme

    def set_theme(self, theme):
        if theme not in ["light", "dark"]:
            raise ValueError("Theme must be either 'light' or 'dark'")
        self.current_theme = theme
        self.themeChanged.emit(self.current_theme)

    def toggle_theme(self):
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.set_theme(new_theme)
        return new_theme

    def apply_theme(self, window: QWidget):
        stylesheet = (
            self.light_theme if self.current_theme == "light" else self.dark_theme
        )
        window.setStyleSheet(stylesheet)
        window.update()
        window.repaint()

    def apply_theme_to_all_windows(self, app):
        for window in app.topLevelWidgets():
            self.apply_theme(window)
