"""
GynTree: This module is responsible for analyzing directory structures.
It provides functionality to traverse directories, collect file information,
and generate both hierarchical and flat representations of the directory structure.
The DirectoryAnalyzer class is the core component for directory analysis operations.
"""

import os
from services.CommentParser import CommentParser

class DirectoryAnalyzer:
    def __init__(self, start_dir, settings_manager):
        self.start_dir = os.path.normpath(start_dir)
        self.settings_manager = settings_manager
        self.comment_parser = CommentParser()

    def analyze_directory(self):
        return self._analyze_recursive(self.start_dir)

    def get_flat_structure(self):
        flat_structure = []
        for root, _, files in os.walk(self.start_dir):
            if self.settings_manager.is_excluded_dir(root):
                continue
            for file in files:
                full_path = os.path.join(root, file)
                if not self.settings_manager.is_excluded_file(full_path):
                    flat_structure.append({
                        'path': full_path,
                        'description': self.comment_parser.get_file_purpose(full_path)
                    })
        return flat_structure

    def _analyze_recursive(self, current_dir):
        structure = {
            'name': os.path.basename(current_dir),
            'type': 'Directory',
            'path': current_dir,
            'children': []
        }

        for item in os.listdir(current_dir):
            full_path = os.path.join(current_dir, item)
            
            if self.settings_manager.is_excluded_dir(full_path) or self.settings_manager.is_excluded_file(full_path):
                continue

            if os.path.isdir(full_path):
                structure['children'].append(self._analyze_recursive(full_path))
            else:
                file_info = {
                    'name': item,
                    'type': 'File',
                    'path': full_path,
                }
                structure['children'].append(file_info)

        return structure