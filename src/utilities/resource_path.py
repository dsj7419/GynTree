import sys
from pathlib import Path


class ResourcePathManager:
    def __init__(self) -> None:
        self._base_path: Path = self._determine_base_path()

    def _determine_base_path(self) -> Path:
        try:
            base_path = Path(getattr(sys, "_MEIPASS"))
        except AttributeError:
            current_file = Path(__file__)
            base_path = current_file.parent.parent.parent
        return base_path

    def get_resource_path(self, relative_path: str) -> str:
        resource_path = self.base_path / relative_path
        src_path = self.base_path / "src" / relative_path
        if src_path.exists():
            return str(src_path)
        if resource_path.exists():
            return str(resource_path)
        raise FileNotFoundError(f"Resource not found: {relative_path}")

    @property
    def base_path(self) -> Path:
        return self._base_path


_manager = ResourcePathManager()


def get_resource_path(relative_path: str) -> str:
    return _manager.get_resource_path(relative_path)
