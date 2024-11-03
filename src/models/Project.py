import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class Project:
    """
    Project model representing a directory analysis project.
    Handles project configuration, validation, and serialization.
    """

    def __init__(
        self,
        name: str,
        start_directory: str,
        root_exclusions: Optional[List[str]] = None,
        excluded_dirs: Optional[List[str]] = None,
        excluded_files: Optional[List[str]] = None,
    ):
        """
        Initialize a new Project instance.

        Args:
            name: Project name
            start_directory: Starting directory path
            root_exclusions: List of root-level exclusions
            excluded_dirs: List of directories to exclude
            excluded_files: List of files to exclude

        Raises:
            ValueError: If name contains invalid characters or directory doesn't exist
        """
        if not self.is_valid_name(name):
            raise ValueError(f"Invalid project name: {name}")

        self._validate_directory(start_directory)

        self.name = name
        self.start_directory = start_directory
        self.root_exclusions = root_exclusions if root_exclusions is not None else []
        self.excluded_dirs = excluded_dirs if excluded_dirs is not None else []
        self.excluded_files = excluded_files if excluded_files is not None else []

    def _validate_directory(self, directory: str) -> None:
        """
        Validate that the directory exists.

        Args:
            directory: Directory path to validate

        Raises:
            ValueError: If directory doesn't exist
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert project details to a dictionary.

        Returns:
            Dictionary containing project data
        """
        return {
            "name": self.name,
            "start_directory": self.start_directory,
            "root_exclusions": self.root_exclusions,
            "excluded_dirs": self.excluded_dirs,
            "excluded_files": self.excluded_files,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """
        Create a Project instance from a dictionary.

        Args:
            data: Dictionary containing project data

        Returns:
            New Project instance
        """
        return cls(
            name=data.get("name"),
            start_directory=data.get("start_directory"),
            root_exclusions=data.get("root_exclusions", []),
            excluded_dirs=data.get("excluded_dirs", []),
            excluded_files=data.get("excluded_files", []),
        )

    @staticmethod
    def is_valid_name(name: str) -> bool:
        """
        Check if a project name is valid.

        Args:
            name: Project name to validate

        Returns:
            True if name is valid, False otherwise
        """
        invalid_chars = set('/\\:*?"<>|')
        return not any(char in invalid_chars for char in name)
