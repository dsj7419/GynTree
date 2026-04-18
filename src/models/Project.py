from pathlib import Path
from typing import Any, Dict, List, Optional


class Project:
    def __init__(
        self,
        name: str,
        start_directory: str,
        root_exclusions: Optional[List[str]] = None,
        excluded_dirs: Optional[List[str]] = None,
        excluded_files: Optional[List[str]] = None,
    ):
        if not self.is_valid_name(name):
            raise ValueError(f"Invalid project name: {name}")
        self._validate_directory(start_directory)
        self.name = name
        self.start_directory = start_directory
        self.root_exclusions = root_exclusions if root_exclusions is not None else []
        self.excluded_dirs = excluded_dirs if excluded_dirs is not None else []
        self.excluded_files = excluded_files if excluded_files is not None else []

    def _validate_directory(self, directory: str) -> None:
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "start_directory": self.start_directory,
            "root_exclusions": self.root_exclusions,
            "excluded_dirs": self.excluded_dirs,
            "excluded_files": self.excluded_files,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        name = data.get("name")
        start_directory = data.get("start_directory")

        if name is None or start_directory is None:
            raise ValueError("Missing required fields: name and start_directory")

        return cls(
            name=name,
            start_directory=start_directory,
            root_exclusions=data.get("root_exclusions", []),
            excluded_dirs=data.get("excluded_dirs", []),
            excluded_files=data.get("excluded_files", []),
        )

    @staticmethod
    def is_valid_name(name: str) -> bool:
        invalid_chars = set('/\\:*?"<>|')
        return not any(char in invalid_chars for char in name)
