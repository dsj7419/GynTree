# GynTree: Provides various utility functions used throughout the GynTree application.

from PyQt5.QtWidgets import QApplication

def copy_to_clipboard(text):
    """Copy text to the system clipboard using PyQt5."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    clipboard = app.clipboard()
    clipboard.setText(text)
