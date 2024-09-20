from PyQt5.QtWidgets import QApplication, QWidget


class WindowManager:
    @staticmethod
    def create_window(widget_class, *args, **kwargs):
        """Create a PyQt5 window for the given widget class."""
        window = widget_class(*args, **kwargs)
        window.show()
        return window
