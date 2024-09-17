# GynTree: Manages the creation and population of tree structures for directory visualization.

import os
from PyQt5.QtWidgets import QTreeWidgetItem

class TreeStructureManager:
    def __init__(self, directory_analyzer, folder_icon, file_icon):
        self.directory_analyzer = directory_analyzer
        self.folder_icon = folder_icon
        self.file_icon = file_icon

    def populate_tree(self, tree_widget):
        """
        Populate the QTreeWidget with the directory structure from the analyzer.
        """
        tree_widget.clear()
        project_name = os.path.basename(self.directory_analyzer.start_dir)
        root_item = QTreeWidgetItem(tree_widget, [project_name, 'Directory'])
        root_item.setIcon(0, self.folder_icon)
        self._populate_item(root_item)

    def _populate_item(self, parent_item):
        """
        Recursively populate the tree structure.
        """
        structure = self.directory_analyzer.get_directory_structure()
        path_dict = self._build_path_dict(structure)
        self._add_items(parent_item, path_dict)

    def _build_path_dict(self, structure):
        """
        Build a hierarchical path dictionary from the directory structure.
        """
        path_dict = {}

        for path, item_type in structure:
            parts = os.path.relpath(path, self.directory_analyzer.start_dir).split(os.sep)
            current_dict = path_dict

            for part in parts[:-1]:
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]

            if item_type == 'Directory':
                if parts[-1] not in current_dict:
                    current_dict[parts[-1]] = {}
            else:
                current_dict[parts[-1]] = 'File'

        return path_dict

    def _add_items(self, parent, path_dict):
        """
        Recursively add items to the QTreeWidget from the path dictionary.
        """
        for name, value in sorted(path_dict.items()):
            if isinstance(value, dict):
                item = QTreeWidgetItem(parent, [name, 'Directory'])
                item.setIcon(0, self.folder_icon)
                self._add_items(item, value) 
            else:
                item = QTreeWidgetItem(parent, [name, 'File'])
                item.setIcon(0, self.file_icon)
