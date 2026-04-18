import logging
import os
import stat
import threading
from typing import Any, Dict, List

from services.DirectoryStructureService import DirectoryStructureService
from services.SettingsManager import SettingsManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DirectoryAnalyzer:
    def __init__(self, start_dir: str, settings_manager: SettingsManager) -> None:
        self.start_dir = start_dir
        self.settings_manager = settings_manager
        self.directory_structure_service = DirectoryStructureService(settings_manager)
        self._stop_event = threading.Event()

    def analyze_directory(self) -> Dict[str, Any]:
        logger.debug(f"Analyzing directory hierarchy for: {self.start_dir}")
        result: Dict[
            str, Any
        ] = self.directory_structure_service.get_hierarchical_structure(
            self.start_dir, self._stop_event
        )

        if "children" in result:
            result["children"] = [
                self._process_child(child) for child in result["children"]
            ]
        return result

    def _check_directory_permissions(self, path: str) -> bool:
        try:
            mode = os.stat(path).st_mode
            return bool(mode & stat.S_IRUSR)
        except (OSError, PermissionError):
            return False

    def _process_child(self, child: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if child["type"] == "directory":
                self._process_directory(child)
            elif child["type"] == "file":
                self._process_file(child)
        except (OSError, PermissionError):
            self._handle_error(child)
        return child

    def _process_directory(self, child: Dict[str, Any]) -> None:
        has_access = self._check_directory_permissions(child["path"])
        if not has_access:
            child["children"] = []
        elif "children" in child:
            child["children"] = [
                self._process_child(grandchild)
                for grandchild in child.get("children", [])
            ]

    def _process_file(self, child: Dict[str, Any]) -> None:
        parent_dir = os.path.dirname(child["path"])
        if not self._check_directory_permissions(parent_dir):
            child["description"] = "No description available"
        else:
            self._check_file_access(child)

    def _check_file_access(self, child: Dict[str, Any]) -> None:
        try:
            if (
                not os.access(child["path"], os.R_OK)
                or os.path.getsize(child["path"]) == 0
            ):
                child["description"] = "No description available"
        except (OSError, PermissionError):
            child["description"] = "No description available"

    def _handle_error(self, child: Dict[str, Any]) -> None:
        if child["type"] == "directory":
            child["children"] = []
        child["description"] = "No description available"

    def get_flat_structure(self) -> List[Dict[str, Any]]:
        logger.debug(f"Generating flat directory structure for: {self.start_dir}")
        result = self.directory_structure_service.get_flat_structure(
            self.start_dir, self._stop_event
        )

        return [
            self._process_flat_item(item)
            for item in result
            if "styles" not in str(item["path"])
        ]

    def _process_flat_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            parent_dir = os.path.dirname(item["path"])
            if (
                not self._check_directory_permissions(parent_dir)
                or not os.access(item["path"], os.R_OK)
                or os.path.getsize(item["path"]) == 0
            ):
                item["description"] = "No description available"
        except (OSError, PermissionError):
            item["description"] = "No description available"
        return item

    def stop(self) -> None:
        self._stop_event.set()
