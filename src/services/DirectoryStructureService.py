import os
import logging
from typing import Dict, Any, List, Optional
from services.CommentParser import CommentParser, DefaultFileReader, DefaultCommentSyntax
from services.SettingsManager import SettingsManager
import threading
from functools import wraps

logger = logging.getLogger(__name__)

def log_error(msg: str, error: Exception, include_trace: bool = False):
    """Centralized error logging with controlled traceback"""
    if include_trace:
        logger.error(msg, exc_info=True)
    else:
        logger.error(f"{msg}: {str(error)}")

def propagate_errors(func):
    """Decorator to properly propagate and handle errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            if func.__name__ == '_analyze_recursive':
                return {
                    'name': os.path.basename(args[1]),
                    'type': 'directory',
                    'path': args[1],
                    'children': [],
                    'error': str(e)
                }
            raise
    return wrapper

def check_stop_event(func):
    """Decorator to check stop event at function entry points"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        stop_event = next((arg for arg in args if isinstance(arg, threading.Event)), None)
        if stop_event and stop_event.is_set():
            logger.debug(f"Operation stopped before {func.__name__}")
            return {} if func.__name__.endswith('structure') else []
        return func(self, *args, **kwargs)
    return wrapper

class DirectoryStructureService:
    """Service for analyzing directory structures and managing file system operations."""
    
    def __init__(self, settings_manager: SettingsManager):
        """Initialize the service with required dependencies."""
        self.settings_manager = settings_manager
        self.comment_parser = CommentParser(DefaultFileReader(), DefaultCommentSyntax())
        self._processing = False
        self._batch_size = 10  # Process files in batches
    
    @check_stop_event
    def get_hierarchical_structure(self, start_dir: str, stop_event: threading.Event) -> Dict[str, Any]:
        """Generate hierarchical directory structure."""
        if not start_dir or not os.path.exists(start_dir):
            return {
                'name': os.path.basename(start_dir) if start_dir else '',
                'type': 'directory',
                'path': start_dir,
                'children': [],
                'error': 'Invalid or non-existent path'
            }
            
        logger.debug(f"Generating hierarchical structure for: {start_dir}")
        
        try:
            # Create base structure
            structure = {
                'name': os.path.basename(start_dir),
                'type': 'directory',
                'path': start_dir,
                'children': []
            }
            
            if stop_event.is_set():
                return {}
            
            if self.settings_manager.is_excluded(start_dir):
                logger.debug(f"Skipping excluded directory: {start_dir}")
                return structure
            
            self._processing = True
            result = self._analyze_recursive(start_dir, stop_event)
            
            if stop_event.is_set():
                return {}
            
            return result if result else structure
            
        except Exception as e:
            logger.error(f"Error generating hierarchical structure: {e}")
            return {
                'name': os.path.basename(start_dir),
                'type': 'directory',
                'path': start_dir,
                'children': [],
                'error': str(e)
            }
        finally:
            self._processing = False

    @check_stop_event
    def _analyze_recursive(self, current_dir: str, stop_event: threading.Event) -> Dict[str, Any]:
        """Recursively analyze directory structure with enhanced stop checking."""
        try:
            if not os.path.exists(current_dir):
                return {
                    'name': os.path.basename(current_dir),
                    'type': 'directory',
                    'path': current_dir,
                    'children': [],
                    'error': 'Directory does not exist'
                }
            
            if self.settings_manager.is_excluded(current_dir):
                logger.debug(f"Skipping excluded directory: {current_dir}")
                return {}
            
            if stop_event.is_set():
                return {}
            
            structure = {
                'name': os.path.basename(current_dir),
                'type': 'directory',
                'path': current_dir,
                'children': [],
                'error': None
            }
            
            try:
                items = os.listdir(current_dir)
                for i in range(0, len(items), self._batch_size):
                    if stop_event.is_set():
                        return {}
                    
                    batch = items[i:i + self._batch_size]
                    for item in batch:
                        if stop_event.is_set():
                            return {}
                        
                        full_path = os.path.join(current_dir, item)
                        if not self.settings_manager.is_excluded(full_path):
                            try:
                                if os.path.isdir(full_path):
                                    child_structure = self._analyze_recursive(full_path, stop_event)
                                    if stop_event.is_set():
                                        return {}
                                    if child_structure:
                                        if child_structure.get('error'):
                                            structure['error'] = child_structure['error']
                                        structure['children'].append(child_structure)
                                else:
                                    description = self._safe_get_file_purpose(full_path)
                                    structure['children'].append({
                                        'name': item,
                                        'type': 'file',
                                        'path': full_path,
                                        'description': description
                                    })
                            except Exception as e:
                                logger.error(f"Error processing {item}: {e}")
                                continue
                
            except PermissionError as e:
                error_msg = f"Permission denied: {str(e)}"
                logger.warning(error_msg)
                structure['error'] = error_msg
            except Exception as e:
                error_msg = f"Error analyzing directory: {str(e)}"
                logger.error(error_msg)
                structure['error'] = error_msg
            
            return structure
            
        except Exception as e:
            logger.error(f"Error in recursive analysis: {e}")
            return {
                'name': os.path.basename(current_dir),
                'type': 'directory',
                'path': current_dir,
                'children': [],
                'error': f"Error analyzing directory: {str(e)}" 
            }
    
    @propagate_errors
    def get_flat_structure(self, start_dir: str, stop_event: threading.Event) -> List[Dict[str, Any]]:
        """Generate flat directory structure.
        
        Args:
            start_dir: Starting directory path
            stop_event: Threading event to control operation
            
        Returns:
            List of dictionaries containing file information
        """
        if not start_dir or not os.path.exists(start_dir):
            logger.error(f"Invalid directory path: {start_dir}")
            return []
            
        logger.debug(f"Generating flat structure for: {start_dir}")
        flat_structure = []
        
        try:
            self._processing = True
            for root, dirs, files in self._walk_directory(start_dir, stop_event):
                if stop_event.is_set():
                    logger.debug("Directory analysis stopped.")
                    return []
                
                for file in files:
                    try:
                        full_path = os.path.join(root, file)
                        if not self.settings_manager.is_excluded(full_path):
                            description = self._safe_get_file_purpose(full_path)
                            flat_structure.append({
                                'path': full_path,
                                'type': 'file',
                                'description': description
                            })
                    except Exception as e:
                        logger.warning(f"Error processing file {file}: {e}", exc_info=True)
                        continue
                        
                if stop_event.is_set():
                    logger.debug("Directory analysis stopped during file processing.")
                    return []
        except Exception as e:
            logger.error(f"Error generating flat structure: {e}", exc_info=True)
            return []
        finally:
            self._processing = False
        
        return flat_structure
    
    def _walk_directory(self, start_dir: str, stop_event: threading.Event):
        """Generator for walking directory structure.
        
        Args:
            start_dir: Starting directory path
            stop_event: Threading event to control operation
            
        Yields:
            Tuple of (root, dirs, files)
        """
        if not os.path.exists(start_dir):
            logger.error(f"Directory does not exist: {start_dir}")
            return
            
        try:
            for root, dirs, files in os.walk(start_dir):
                if stop_event.is_set():
                    logger.debug("Directory walk stopped.")
                    return
                
                try:
                    if stop_event.is_set():  # Add this additional check
                        return
                    dirs[:] = [d for d in dirs if not self.settings_manager.is_excluded(os.path.join(root, d))]
                    yield root, dirs, files
                except Exception as e:
                    logger.warning(f"Error processing directory {root}: {e}", exc_info=True)
                    continue
        except Exception as e:
            logger.error(f"Error walking directory structure: {e}", exc_info=True)
            return
    
    def _safe_get_file_purpose(self, file_path: str) -> Optional[str]:
        """Safely get file purpose with error handling.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File purpose description or None on error
        """
        if not os.path.exists(file_path):
            return None
            
        try:
            return self.comment_parser.get_file_purpose(file_path)
        except Exception as e:
            logger.warning(f"Error getting file purpose for {file_path}: {e}", exc_info=True)
            return None