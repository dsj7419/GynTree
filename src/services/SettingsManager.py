import fnmatch
import json
import logging
import os
from typing import Any, Dict, List, Optional, Set

from models.Project import Project
from services.ExclusionAggregator import ExclusionAggregator

logger = logging.getLogger(__name__)


class SettingsManager:
    config_dir: str = "config"  # Class variable for config directory

    def __init__(self, project: Project):
        """
        Initialize SettingsManager with a project.

        Args:
            project: Project instance containing initial settings
        """
        self.project = project
        self.config_path = os.path.join(
            self.config_dir, "projects", f"{self.project.name}.json"
        )
        self.exclusion_aggregator = ExclusionAggregator()
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from file or initialize with defaults.

        Returns:
            Dict containing settings with all required keys
        """
        settings = {}
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as file:
                    settings = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load settings file: {e}")

        # Initialize with project values first
        default_settings = {
            "root_exclusions": list(self.project.root_exclusions)
            if self.project.root_exclusions
            else [],
            "excluded_dirs": list(self.project.excluded_dirs)
            if self.project.excluded_dirs
            else [],
            "excluded_files": list(self.project.excluded_files)
            if self.project.excluded_files
            else [],
            "theme_preference": "light",
        }

        # Merge with existing settings, preserving defaults if keys don't exist
        for key, default_value in default_settings.items():
            if key not in settings or not settings[key]:
                settings[key] = default_value
            elif isinstance(default_value, list) and isinstance(settings[key], list):
                # Ensure unique values in lists while preserving order
                settings[key] = list(dict.fromkeys(settings[key] + default_value))

        return settings

    def get_theme_preference(self) -> str:
        """Get current theme preference."""
        return self.settings.get("theme_preference", "light")

    def set_theme_preference(self, theme: str):
        """Set theme preference and save settings."""
        self.settings["theme_preference"] = theme
        self.save_settings()

    def get_root_exclusions(self) -> List[str]:
        """Get normalized root exclusions."""
        return [os.path.normpath(d) for d in self.settings.get("root_exclusions", [])]

    def get_excluded_dirs(self) -> List[str]:
        """Get normalized excluded directories."""
        return [os.path.normpath(d) for d in self.settings.get("excluded_dirs", [])]

    def get_excluded_files(self) -> List[str]:
        """Get normalized excluded files."""
        return [os.path.normpath(f) for f in self.settings.get("excluded_files", [])]

    def get_all_exclusions(self) -> Dict[str, Set[str]]:
        """Get all exclusions as sets."""
        return {
            "root_exclusions": set(self.get_root_exclusions()),
            "excluded_dirs": set(self.get_excluded_dirs()),
            "excluded_files": set(self.get_excluded_files()),
        }

    def update_settings(self, new_settings: Dict[str, List[str]]):
        """Update settings with new values and save."""
        for key, value in new_settings.items():
            if key in self.settings:
                # Normalize paths in lists
                if isinstance(value, list):
                    self.settings[key] = [os.path.normpath(item) for item in value]
                else:
                    self.settings[key] = value
        self.save_settings()

    def save_settings(self):
        """Save current settings to file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as file:
            json.dump(self.settings, file, indent=4)
        logger.debug(f"Settings saved to {self.config_path}")

    def is_excluded(self, path: str) -> bool:
        """
        Check if a path should be excluded.

        Args:
            path: Path to check

        Returns:
            True if path should be excluded, False otherwise
        """
        normalized_path = os.path.normpath(path)

        # First check if it's in an excluded directory
        if os.path.isfile(normalized_path):
            if self.is_excluded_dir(os.path.dirname(normalized_path)):
                return True
            if self.is_excluded_file(normalized_path):
                return True
        else:
            if self.is_excluded_dir(normalized_path):
                return True

        # Check root exclusions
        return self.is_root_excluded(normalized_path)

    def is_root_excluded(self, path: str) -> bool:
        """Check if path matches root exclusions."""
        relative_path = self._get_relative_path(path)
        path_parts = relative_path.split(os.sep)

        for excluded in self.get_root_exclusions():
            excluded = os.path.normpath(excluded)
            if "**" in excluded:
                if fnmatch.fnmatch(relative_path, excluded):
                    logger.debug(
                        f"Root excluded (wildcard): {path} (matched {excluded})"
                    )
                    return True
            elif excluded in path_parts:
                logger.debug(f"Root excluded: {path} (matched {excluded})")
                return True
            elif fnmatch.fnmatch(relative_path, excluded):
                logger.debug(f"Root excluded (pattern): {path} (matched {excluded})")
                return True
        return False

    def is_excluded_dir(self, path: str) -> bool:
        """Check if path matches excluded directories."""
        if not path:
            return False

        normalized_path = os.path.normpath(path)
        relative_path = self._get_relative_path(normalized_path)
        basename = os.path.basename(normalized_path)

        for excluded_dir in self.get_excluded_dirs():
            excluded_dir = os.path.normpath(excluded_dir)
            # First try exact name match (handles basic patterns like "dir_0")
            if fnmatch.fnmatch(basename, excluded_dir):
                logger.debug(f"Excluded directory: {path} (matched {excluded_dir})")
                return True
            # Then try relative path match
            if fnmatch.fnmatch(relative_path, excluded_dir):
                logger.debug(f"Excluded directory: {path} (matched {excluded_dir})")
                return True
            # Finally check if path is inside excluded directory
            try:
                relative_to_excluded = os.path.relpath(
                    normalized_path,
                    os.path.join(self.project.start_directory, excluded_dir),
                )
                if not relative_to_excluded.startswith(".."):
                    logger.debug(
                        f"Path is inside excluded directory: {path} (inside {excluded_dir})"
                    )
                    return True
            except ValueError:
                continue
        return False

    def is_excluded_file(self, path: str) -> bool:
        """
        Check if path matches excluded files.

        Args:
            path: Path to check

        Returns:
            True if path matches an excluded file pattern, False otherwise
        """
        if not path:
            return False

        normalized_path = os.path.normpath(path)

        # First check if the file is in an excluded directory
        if self.is_excluded_dir(os.path.dirname(normalized_path)):
            return True

        # Get both the full path and just the filename for pattern matching
        relative_path = self._get_relative_path(normalized_path)
        filename = os.path.basename(normalized_path)

        for excluded_file in self.get_excluded_files():
            excluded_file = os.path.normpath(excluded_file)

            # Match against both full relative path and just filename
            if fnmatch.fnmatch(relative_path, excluded_file) or fnmatch.fnmatch(
                filename, excluded_file
            ):
                logger.debug(f"Excluded file: {path} (matched {excluded_file})")
                return True

            # Handle patterns with directory parts
            if os.sep in excluded_file:
                if fnmatch.fnmatch(relative_path, excluded_file):
                    logger.debug(
                        f"Excluded file (with path): {path} (matched {excluded_file})"
                    )
                    return True

            # Handle simple patterns (e.g. *.log)
            elif "*" in excluded_file or "?" in excluded_file:
                if fnmatch.fnmatch(filename, excluded_file):
                    logger.debug(
                        f"Excluded file (pattern): {path} (matched {excluded_file})"
                    )
                    return True

        return False

    def _get_relative_path(self, path: str) -> str:
        """Get path relative to project start directory."""
        try:
            return os.path.relpath(path, self.project.start_directory)
        except ValueError:
            return path

    def add_excluded_dir(self, directory: str) -> bool:
        """Add directory to excluded_dirs."""
        normalized = os.path.normpath(directory)
        current_dirs = set(self.get_excluded_dirs())
        if normalized not in current_dirs:
            current_dirs.add(normalized)
            self.settings["excluded_dirs"] = list(current_dirs)
            self.save_settings()
            return True
        return False

    def add_excluded_file(self, file: str) -> bool:
        """Add file to excluded_files."""
        normalized = os.path.normpath(file)
        current_files = set(self.get_excluded_files())
        if normalized not in current_files:
            current_files.add(normalized)
            self.settings["excluded_files"] = list(current_files)
            self.save_settings()
            return True
        return False

    def remove_excluded_dir(self, directory: str) -> bool:
        """Remove directory from excluded_dirs."""
        normalized = os.path.normpath(directory)
        current_dirs = set(self.get_excluded_dirs())
        if normalized in current_dirs:
            current_dirs.remove(normalized)
            self.settings["excluded_dirs"] = list(current_dirs)
            self.save_settings()
            return True
        return False

    def remove_excluded_file(self, file: str) -> bool:
        """Remove file from excluded_files."""
        normalized = os.path.normpath(file)
        current_files = set(self.get_excluded_files())
        if normalized in current_files:
            current_files.remove(normalized)
            self.settings["excluded_files"] = list(current_files)
            self.save_settings()
            return True
        return False

    def add_root_exclusion(self, exclusion: str) -> bool:
        """Add root exclusion."""
        normalized = os.path.normpath(exclusion)
        current_exclusions = set(self.get_root_exclusions())
        if normalized not in current_exclusions:
            current_exclusions.add(normalized)
            self.settings["root_exclusions"] = list(current_exclusions)
            self.save_settings()
            return True
        return False

    def remove_root_exclusion(self, exclusion: str) -> bool:
        """Remove root exclusion."""
        normalized = os.path.normpath(exclusion)
        current_exclusions = set(self.get_root_exclusions())
        if normalized in current_exclusions:
            current_exclusions.remove(normalized)
            self.settings["root_exclusions"] = list(current_exclusions)
            self.save_settings()
            return True
        return False
