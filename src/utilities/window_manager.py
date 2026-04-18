from typing import Any, Type, TypeVar

from PyQt5.QtWidgets import QWidget

T = TypeVar("T", bound=QWidget)


class WindowManager:
    @staticmethod
    def create_window(widget_class: Type[T], *args: Any, **kwargs: Any) -> T:
        window = widget_class(*args, **kwargs)
        window.show()
        return window
