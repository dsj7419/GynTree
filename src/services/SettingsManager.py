# GynTree: Handles application and project settings, including reading and writing configurations.

import os
import json

class SettingsManager:
    def __init__(self, project):
        self.project = project
        self.config_path = os.path.join('config', 'projects', f'{self.project.name}.json')
        self.settings = self.load_settings()

    def load_settings(self):
        try:
            with open(self.config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {
                'excluded_dirs': self.project.excluded_dirs,
                'excluded_files': self.project.excluded_files
            }

    def get_excluded_dirs(self):
        return [os.path.normpath(d) for d in self.settings.get('excluded_dirs', [])]

    def get_excluded_files(self):
        return [os.path.normpath(f) for f in self.settings.get('excluded_files', [])]

    def update_settings(self, new_settings):
        self.settings.update(new_settings)
        self.save_settings()

    def save_settings(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as file:
            json.dump(self.settings, file, indent=4)

    def is_excluded_dir(self, path):
        """
        Checks if the given directory path is excluded.
        """
        path = os.path.normpath(path)
        return any(
            os.path.commonpath([path, excluded_dir]) == excluded_dir
            for excluded_dir in self.get_excluded_dirs()
        )

    def is_excluded_file(self, path):
        """
        Checks if the given file path is excluded.
        """
        path = os.path.normpath(path)
        return path in self.get_excluded_files()
