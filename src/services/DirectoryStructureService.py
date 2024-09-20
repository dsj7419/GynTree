import os
import logging
from typing import Dict, Any, List
from services.CommentParser import CommentParser, DefaultFileReader, DefaultCommentSyntax
from services.SettingsManager import SettingsManager
import threading

logger = logging.getLogger(__name__)

class DirectoryStructureService:
    def __init__(self, settings_manager: SettingsManager):
        self.settings_manager = settings_manager
        self.comment_parser = CommentParser(DefaultFileReader(), DefaultCommentSyntax())

    def get_hierarchical_structure(self, start_dir: str, stop_event: threading.Event) -> Dict[str, Any]:
        logger.debug(f"Generating hierarchical structure for: {start_dir}")
        return self._analyze_recursive(start_dir, stop_event)

    def get_flat_structure(self, start_dir: str, stop_event: threading.Event) -> List[Dict[str, Any]]:
        logger.debug(f"Generating flat structure for: {start_dir}")
        flat_structure = []
        for root, dirs, files in os.walk(start_dir):
            if stop_event.is_set():
                logger.debug("Directory analysis stopped.")
                return flat_structure
            
            dirs[:] = [d for d in dirs if not self.settings_manager.is_excluded(os.path.join(root, d))]
            
            if self.settings_manager.is_excluded(root):
                continue
            
            for file in files:
                full_path = os.path.join(root, file)
                if self.settings_manager.is_excluded(full_path):
                    logger.debug(f"Excluding {full_path}")
                    continue
                flat_structure.append({
                    'path': full_path,
                    'type': 'File',
                    'description': self.comment_parser.get_file_purpose(full_path)
                })
        return flat_structure

    def _analyze_recursive(self, current_dir: str, stop_event: threading.Event) -> Dict[str, Any]:
        if stop_event.is_set():
            logger.debug("Directory analysis stopped.")
            return {}
        if self.settings_manager.is_excluded(current_dir):
            logger.debug(f"Skipping excluded directory: {current_dir}")
            return {}
        structure = {
            'name': os.path.basename(current_dir),
            'type': 'Directory',
            'path': current_dir,
            'children': []
        }
        try:
            for item in os.listdir(current_dir):
                if stop_event.is_set():
                    logger.debug("Directory analysis stopped.")
                    return structure
                full_path = os.path.join(current_dir, item)
                
                if self.settings_manager.is_excluded(full_path):
                    logger.debug(f"Skipping excluded path: {full_path}")
                    continue
                if os.path.isdir(full_path):
                    child_structure = self._analyze_recursive(full_path, stop_event)
                    if child_structure:
                        structure['children'].append(child_structure)
                else:
                    file_info = {
                        'name': item,
                        'type': 'File',
                        'path': full_path,
                        'description': self.comment_parser.get_file_purpose(full_path)
                    }
                    structure['children'].append(file_info)
        except PermissionError as e:
            logger.warning(f"Permission denied: {current_dir} - {e}")
        except Exception as e:
            logger.error(f"Error analyzing {current_dir}: {e}")
        return structure