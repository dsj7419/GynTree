import os
import json
import fnmatch
import logging
from typing import List, Dict, Set
from models.Project import Project
from services.ExclusionAggregator import ExclusionAggregator

logger = logging.getLogger(__name__)

class SettingsManager:
    def __init__(self, project: Project):
        self.project = project
        self.config_path = os.path.join('config', 'projects', f"{self.project.name}.json")
        self.settings = self.load_settings()
        self.exclusion_aggregator = ExclusionAggregator()

    def load_settings(self) -> Dict[str, List[str]]:
        try:
            with open(self.config_path, 'r') as file:
                settings = json.load(file)
        except FileNotFoundError:
            settings = {}

        default_settings = {
            'root_exclusions': self.project.root_exclusions or [],
            'excluded_dirs': self.project.excluded_dirs or [],
            'excluded_files': self.project.excluded_files or [],
            'theme_preference': 'light'
        }

        for key, value in default_settings.items():
            if key not in settings:
                settings[key] = value

        return settings
    
    def get_theme_preference(self) -> str:
        return self.settings.get('theme_preference', 'light')

    def set_theme_preference(self, theme: str):
        self.settings['theme_preference'] = theme
        self.save_settings()

    def get_root_exclusions(self) -> List[str]:
        return [os.path.normpath(d) for d in self.settings.get('root_exclusions', [])]

    def get_excluded_dirs(self) -> List[str]:
        return [os.path.normpath(d) for d in self.settings.get('excluded_dirs', [])]

    def get_excluded_files(self) -> List[str]:
        return [os.path.normpath(f) for f in self.settings.get('excluded_files', [])]

    def get_all_exclusions(self) -> Dict[str, Set[str]]:
        return {
            'root_exclusions': set(self.settings.get('root_exclusions', [])),
            'excluded_dirs': set(self.settings.get('excluded_dirs', [])),
            'excluded_files': set(self.settings.get('excluded_files', []))
        }

    def update_settings(self, new_settings: Dict[str, List[str]]):
        for key, value in new_settings.items():
            if key in self.settings:
                self.settings[key] = value
        self.save_settings()

    def save_settings(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as file:
            json.dump(self.settings, file, indent=4)
        logger.debug(f"Settings saved to {self.config_path}")

    def is_excluded(self, path: str) -> bool:
        return (self.is_root_excluded(path) or
                self.is_excluded_dir(path) or
                self.is_excluded_file(path))

    def is_root_excluded(self, path: str) -> bool:
        relative_path = self._get_relative_path(path)
        path_parts = relative_path.split(os.sep)
        for excluded in self.get_root_exclusions():
            if '**' in excluded:
                if fnmatch.fnmatch(relative_path, excluded):
                    logger.debug(f"Root excluded (wildcard): {path} (matched {excluded})")
                    return True
            elif excluded in path_parts:
                logger.debug(f"Root excluded: {path} (matched {excluded})")
                return True
            elif fnmatch.fnmatch(relative_path, excluded):
                logger.debug(f"Root excluded (pattern): {path} (matched {excluded})")
                return True
        return False

    def is_excluded_dir(self, path: str) -> bool:
        if self.is_root_excluded(path):
            return True
        relative_path = self._get_relative_path(path)
        for excluded_dir in self.get_excluded_dirs():
            if fnmatch.fnmatch(relative_path, excluded_dir):
                logger.debug(f"Excluded directory: {path} (matched {excluded_dir})")
                return True
        return False

    def is_excluded_file(self, path: str) -> bool:
        if self.is_root_excluded(os.path.dirname(path)):
            return True
        relative_path = self._get_relative_path(path)
        for excluded_file in self.get_excluded_files():
            if fnmatch.fnmatch(relative_path, excluded_file):
                logger.debug(f"Excluded file: {path} (matched {excluded_file})")
                return True
        return False

    def _get_relative_path(self, path: str) -> str:
        return os.path.relpath(path, self.project.start_directory)
    

    def add_excluded_dir(self, directory: str) -> bool:
        """
        Adds a directory to excluded_dirs if not already present.
        Returns True if added, False if already exists.
        """
        current_dirs = set(self.get_excluded_dirs())
        if directory not in current_dirs:
            current_dirs.add(directory)
            self.update_settings({'excluded_dirs': list(current_dirs)})
            return True
        return False

    def add_excluded_file(self, file: str) -> bool:
        """
        Adds a file to excluded_files if not already present.
        Returns True if added, False if already exists.
        """
        current_files = set(self.get_excluded_files())
        if file not in current_files:
            current_files.add(file)
            self.update_settings({'excluded_files': list(current_files)})
            return True
        return False

    def remove_excluded_dir(self, directory: str) -> bool:
        """
        Removes a directory from excluded_dirs if present.
        Returns True if removed, False if not found.
        """
        current_dirs = set(self.get_excluded_dirs())
        if directory in current_dirs:
            current_dirs.remove(directory)
            self.update_settings({'excluded_dirs': list(current_dirs)})
            return True
        return False

    def remove_excluded_file(self, file: str) -> bool:
        """
        Removes a file from excluded_files if present.
        Returns True if removed, False if not found.
        """
        current_files = set(self.get_excluded_files())
        if file in current_files:
            current_files.remove(file)
            self.update_settings({'excluded_files': list(current_files)})
            return True
        return False

    def add_root_exclusion(self, exclusion: str) -> bool:
        """
        Adds a root exclusion if not already present.
        Returns True if added, False if already exists.
        """
        current_root_exclusions = set(self.get_root_exclusions())
        if exclusion not in current_root_exclusions:
            current_root_exclusions.add(exclusion)
            self.update_settings({'root_exclusions': list(current_root_exclusions)})
            return True
        return False

    def remove_root_exclusion(self, exclusion: str) -> bool:
        """
        Removes a root exclusion if present.
        Returns True if removed, False if not found.
        """
        current_root_exclusions = set(self.get_root_exclusions())
        if exclusion in current_root_exclusions:
            current_root_exclusions.remove(exclusion)
            self.update_settings({'root_exclusions': list(current_root_exclusions)})
            return True
        return False