from typing import Dict, Set


class ExclusionManagerService:
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager

    def get_aggregated_exclusions(self) -> str:
        """
        Returns a formatted string of aggregated exclusions for display.
        """
        exclusions = self.settings_manager.get_all_exclusions()
        lines = []
        # Root Exclusions
        root_exclusions = exclusions.get("root_exclusions", set())
        if root_exclusions:
            lines.append("Root Exclusions:")
            for path in sorted(root_exclusions):
                lines.append(f"  - {path}")
        # Excluded Directories
        excluded_dirs = exclusions.get("excluded_dirs", set())
        if excluded_dirs:
            lines.append("\nExcluded Directories:")
            for path in sorted(excluded_dirs):
                lines.append(f"  - {path}")
        # Excluded Files
        excluded_files = exclusions.get("excluded_files", set())
        if excluded_files:
            lines.append("\nExcluded Files:")
            for path in sorted(excluded_files):
                lines.append(f"  - {path}")
        return "\n".join(lines)

    def get_detailed_exclusions(self) -> Dict[str, Set[str]]:
        """
        Returns a dictionary of detailed exclusions categorized by type.
        """
        return self.settings_manager.get_all_exclusions()

    def add_directory(self, directory: str) -> bool:
        """
        Adds a directory to excluded_dirs if not already present.
        Returns True if added, False if already exists.
        """
        current_dirs = set(self.settings_manager.get_excluded_dirs())
        if directory in current_dirs:
            return False
        current_dirs.add(directory)
        self.settings_manager.update_settings({"excluded_dirs": list(current_dirs)})
        return True

    def add_file(self, file: str) -> bool:
        """
        Adds a file to excluded_files if not already present.
        Returns True if added, False if already exists.
        """
        current_files = set(self.settings_manager.get_excluded_files())
        if file in current_files:
            return False
        current_files.add(file)
        self.settings_manager.update_settings({"excluded_files": list(current_files)})
        return True

    def remove_directory(self, directory: str) -> bool:
        """
        Removes a directory from excluded_dirs if present.
        Returns True if removed, False if not found.
        """
        current_dirs = set(self.settings_manager.get_excluded_dirs())
        if directory not in current_dirs:
            return False
        current_dirs.remove(directory)
        self.settings_manager.update_settings({"excluded_dirs": list(current_dirs)})
        return True

    def remove_file(self, file: str) -> bool:
        """
        Removes a file from excluded_files if present.
        Returns True if removed, False if not found.
        """
        current_files = set(self.settings_manager.get_excluded_files())
        if file not in current_files:
            return False
        current_files.remove(file)
        self.settings_manager.update_settings({"excluded_files": list(current_files)})
        return True

    def save_exclusions(self):
        """
        Saves the current settings. (Assuming SettingsManager handles persistence)
        """
        self.settings_manager.save_settings()
