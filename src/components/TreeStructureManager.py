import os
from typing import Any, Dict, List, Tuple, TypedDict, Union

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem


class DirectoryDict(TypedDict, total=False):
    __entries__: Dict[str, Union["DirectoryDict", str]]


class TreeStructureManager:
    def __init__(
        self, directory_analyzer: Any, folder_icon: QIcon, file_icon: QIcon
    ) -> None:
        self.directory_analyzer = directory_analyzer
        self.folder_icon = folder_icon
        self.file_icon = file_icon

    def populate_tree(self, tree_widget: QTreeWidget) -> None:
        tree_widget.clear()
        project_name = os.path.basename(self.directory_analyzer.start_dir)
        root_item = QTreeWidgetItem(tree_widget, [project_name, "Directory"])
        root_item.setIcon(0, self.folder_icon)
        self._populate_item(root_item)

    def _populate_item(self, parent_item: QTreeWidgetItem) -> None:
        structure = self.directory_analyzer.get_directory_structure()
        path_dict = self._build_path_dict(structure)
        self._add_items(parent_item, path_dict)

    def _build_path_dict(
        self, structure: List[Tuple[str, str]]
    ) -> Dict[str, Union[Dict[str, Any], str]]:
        path_dict: Dict[str, Union[Dict[str, Any], str]] = {}
        for path, item_type in structure:
            parts = os.path.relpath(path, self.directory_analyzer.start_dir).split(
                os.sep
            )
            # Rename current_dict to current_level to avoid redefinition
            current_level: Dict[str, Union[Dict[str, Any], str]] = path_dict
            for part in parts[:-1]:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]  # type: ignore
            if item_type == "Directory":
                if parts[-1] not in current_level:
                    current_level[parts[-1]] = {}
            else:
                current_level[parts[-1]] = "File"
        return path_dict

    def _add_items(
        self, parent: QTreeWidgetItem, path_dict: Dict[str, Union[Dict[str, Any], str]]
    ) -> None:
        for name, value in sorted(path_dict.items()):
            if isinstance(value, dict):
                item = QTreeWidgetItem(parent, [name, "Directory"])
                item.setIcon(0, self.folder_icon)
                self._add_items(item, value)
            else:
                item = QTreeWidgetItem(parent, [name, "File"])
                item.setIcon(0, self.file_icon)
