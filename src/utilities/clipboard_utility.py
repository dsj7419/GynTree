from PyQt5.QtGui import QClipboard
from PyQt5.QtWidgets import QApplication


def copy_to_clipboard(text: str) -> None:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        clipboard: QClipboard = app.clipboard()
        clipboard.setText(text)
