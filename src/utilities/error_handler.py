import sys
import logging
import traceback
from functools import wraps
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)

class ErrorHandler(QObject):
    error_occurred = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.error_occurred.connect(self.show_error_dialog)

    def global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions globally"""
        error_msg = f"An unexpected error occurred:\n{exc_type.__name__}: {exc_value}"
        detailed_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        self.error_occurred.emit("Critical Error", error_msg)
        
        logger.debug(f"Detailed error traceback:\n{detailed_msg}")

    def show_error_dialog(self, title, message):
        """Show an error dialog with the given title and message"""
        QTimer.singleShot(0, lambda: QMessageBox.critical(None, title, message))

def handle_exception(func):
    """Decorator to handle exceptions in individual methods"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {str(e)}")
            error_msg = f"An error occurred in {func.__name__}:\n{str(e)}"
            QMessageBox.critical(None, "Error", error_msg)
    return wrapper

error_handler = ErrorHandler()

sys.excepthook = error_handler.global_exception_handler