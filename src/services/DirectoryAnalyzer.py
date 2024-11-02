import logging
from typing import Dict, Any, List
from pathlib import Path
from services.DirectoryStructureService import DirectoryStructureService
import threading
import os
import stat

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DirectoryAnalyzer:
    def __init__(self, start_dir: str, settings_manager):
        self.start_dir = start_dir
        self.settings_manager = settings_manager
        self.directory_structure_service = DirectoryStructureService(settings_manager)
        self._stop_event = threading.Event()

    def analyze_directory(self) -> Dict[str, Any]:
        """
        Analyze directory and return hierarchical structure.
        """
        logger.debug(f"Analyzing directory hierarchy for: {self.start_dir}")
        result = self.directory_structure_service.get_hierarchical_structure(self.start_dir, self._stop_event)
        
        if 'children' in result:
            result['children'] = [
                self._process_child(child) 
                for child in result['children']
            ]
        return result

    def _check_directory_permissions(self, path: str) -> bool:
        """Check directory permissions."""
        try:
            mode = os.stat(path).st_mode
            return bool(mode & stat.S_IRUSR)
        except (OSError, PermissionError):
            return False

    def _process_child(self, child: Dict[str, Any]) -> Dict[str, Any]:
        """Process a child node, handling permissions and errors."""
        try:
            if child['type'] == 'directory':
                # Check directory permissions first
                has_access = self._check_directory_permissions(child['path'])
                if not has_access:
                    child['children'] = []
                elif 'children' in child:
                    processed_children = []
                    for grandchild in child.get('children', []):
                        processed = self._process_child(grandchild)
                        if has_access:
                            processed['description'] = processed.get('description', 'No description available')
                        processed_children.append(processed)
                    child['children'] = processed_children
            elif child['type'] == 'file':
                # For files, always set description to "No description available" if parent has no permissions
                parent_dir = os.path.dirname(child['path'])
                if not self._check_directory_permissions(parent_dir):
                    child['description'] = "No description available"
                else:
                    try:
                        if not os.access(child['path'], os.R_OK) or os.path.getsize(child['path']) == 0:
                            child['description'] = "No description available"
                    except (OSError, PermissionError):
                        child['description'] = "No description available"
        except (OSError, PermissionError):
            if child['type'] == 'directory':
                child['children'] = []
            child['description'] = "No description available"
        
        return child

    def get_flat_structure(self) -> List[Dict[str, Any]]:
        """Get flat structure of directory."""
        logger.debug(f"Generating flat directory structure for: {self.start_dir}")
        result = self.directory_structure_service.get_flat_structure(self.start_dir, self._stop_event)
        
        return [
            self._process_flat_item(item)
            for item in result
            if 'styles' not in str(item['path'])
        ]

    def _process_flat_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a flat structure item."""
        try:
            parent_dir = os.path.dirname(item['path'])
            if not self._check_directory_permissions(parent_dir) or \
               not os.access(item['path'], os.R_OK) or \
               os.path.getsize(item['path']) == 0:
                item['description'] = "No description available"
        except (OSError, PermissionError):
            item['description'] = "No description available"
        return item

    def stop(self):
        """Signal analysis to stop."""
        self._stop_event.set()