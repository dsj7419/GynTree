import os
from services.CommentParser import CommentParser

class DirectoryAnalyzer:
    def __init__(self, start_dir, settings_manager):
        self.start_dir = os.path.normpath(start_dir)  # Normalize the starting directory path
        self.settings_manager = settings_manager

    def analyze_directory(self):
        """
        Traverse the directory, analyze files, and exclude files based on the settings.
        """
        tree = {}

        for root, dirs, files in os.walk(self.start_dir):
            root = os.path.normpath(root)  # Normalize root directory path

            # Exclude directories
            if self.settings_manager.is_excluded_dir(root):
                dirs[:] = []  # Clear subdirectories if the root is excluded
                continue

            # Filter out excluded subdirectories
            dirs[:] = [d for d in dirs if not self.settings_manager.is_excluded_dir(os.path.join(root, d))]

            # Process files
            for file in files:
                filepath = os.path.join(root, file)
                filepath = os.path.normpath(filepath)  # Normalize file path

                # Check if the file is excluded
                if not self.settings_manager.is_excluded_file(filepath):
                    # Add files that are not excluded
                    tree[filepath] = CommentParser.get_file_purpose(filepath)

        return tree

    def get_directory_structure(self):
        """
        Get the structure of the directory while excluding specified directories and files.
        """
        structure = []

        for root, dirs, files in os.walk(self.start_dir):
            root = os.path.normpath(root)  # Normalize root directory path

            # Exclude directories
            if self.settings_manager.is_excluded_dir(root):
                dirs[:] = []  # Clear subdirectories if the root is excluded
                continue

            # Filter out excluded subdirectories
            dirs[:] = [d for d in dirs if not self.settings_manager.is_excluded_dir(os.path.join(root, d))]

            # Add directories to structure
            for name in dirs:
                full_path = os.path.join(root, name)
                full_path = os.path.normpath(full_path)  # Normalize path
                if not self.settings_manager.is_excluded_dir(full_path):
                    structure.append((full_path, 'Directory'))

            # Add files to structure
            for file in files:
                full_path = os.path.join(root, file)
                full_path = os.path.normpath(full_path)  # Normalize file path
                if not self.settings_manager.is_excluded_file(full_path):
                    structure.append((full_path, 'File'))

        return structure
