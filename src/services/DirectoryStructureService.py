import logging
import os
import threading
from functools import wraps
from typing import Any, Callable, Dict, Generator, List, Optional, TypeVar, Union, cast

from services.CommentParser import (
    CommentParser,
    DefaultCommentSyntax,
    DefaultFileReader,
)
from services.SettingsManager import SettingsManager

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])
ReturnT = Union[Dict[str, Any], List[Any]]


def log_error(msg: str, error: Exception, include_trace: bool = False) -> None:
    if include_trace:
        logger.error(msg, exc_info=True)
    else:
        logger.error(f"{msg}: {str(error)}")


def propagate_errors(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> ReturnT:
        try:
            result = func(*args, **kwargs)
            # Ensure we're returning the correct type
            if isinstance(result, (dict, list)):
                return result
            raise TypeError(f"Unexpected return type from {func.__name__}")
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            if func.__name__ == "_analyze_recursive":
                return cast(
                    ReturnT,
                    {
                        "name": os.path.basename(args[1]),
                        "type": "directory",
                        "path": args[1],
                        "children": [],
                        "error": str(e),
                    },
                )
            raise

    return cast(F, wrapper)


def check_stop_event(func: F) -> F:
    @wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> ReturnT:
        stop_event = next(
            (arg for arg in args if isinstance(arg, threading.Event)), None
        )
        if stop_event and stop_event.is_set():
            logger.debug(f"Operation stopped before {func.__name__}")
            return cast(ReturnT, {} if func.__name__.endswith("structure") else [])
        result = func(self, *args, **kwargs)
        if isinstance(result, (dict, list)):
            return result
        raise TypeError(f"Unexpected return type from {func.__name__}")

    return cast(F, wrapper)


class DirectoryStructureService:
    def __init__(self, settings_manager: SettingsManager) -> None:
        self.settings_manager = settings_manager
        self.comment_parser = CommentParser(DefaultFileReader(), DefaultCommentSyntax())
        self._processing = False
        self._batch_size = 10

    @check_stop_event
    def get_hierarchical_structure(
        self, start_dir: str, stop_event: threading.Event
    ) -> Dict[str, Any]:
        if not start_dir or not os.path.exists(start_dir):
            structure: Dict[str, Any] = {
                "name": os.path.basename(start_dir) if start_dir else "",
                "type": "directory",
                "path": start_dir,
                "children": [],
                "error": "Invalid or non-existent path",
            }
            return structure

        logger.debug(f"Generating hierarchical structure for: {start_dir}")

        try:
            structure = {
                "name": os.path.basename(start_dir),
                "type": "directory",
                "path": start_dir,
                "children": [],
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
            error_structure: Dict[str, Any] = {
                "name": os.path.basename(start_dir),
                "type": "directory",
                "path": start_dir,
                "children": [],
                "error": str(e),
            }
            return error_structure
        finally:
            self._processing = False

    def _create_error_structure(
        self, current_dir: str, error_msg: str
    ) -> Dict[str, Any]:
        return {
            "name": os.path.basename(current_dir),
            "type": "directory",
            "path": current_dir,
            "children": [],
            "error": error_msg,
        }

    def _create_base_structure(self, current_dir: str) -> Dict[str, Any]:
        return {
            "name": os.path.basename(current_dir),
            "type": "directory",
            "path": current_dir,
            "children": [],
            "error": None,
        }

    def _process_file(self, file_path: str, file_name: str) -> Dict[str, Any]:
        description = self._safe_get_file_purpose(file_path)
        return {
            "name": file_name,
            "type": "file",
            "path": file_path,
            "description": description,
        }

    def _process_directory_items(
        self, items: List[str], current_dir: str, stop_event: threading.Event
    ) -> List[Dict[str, Any]]:
        children = []
        for i in range(0, len(items), self._batch_size):
            if stop_event.is_set():
                return []

            batch = items[i : i + self._batch_size]
            batch_children = self._process_batch(batch, current_dir, stop_event)
            if stop_event.is_set():
                return []
            children.extend(batch_children)
        return children

    def _process_batch(
        self, batch: List[str], current_dir: str, stop_event: threading.Event
    ) -> List[Dict[str, Any]]:
        batch_children = []
        for item in batch:
            if stop_event.is_set():
                return []

            full_path = os.path.join(current_dir, item)
            if not self.settings_manager.is_excluded(full_path):
                try:
                    child_structure = self._process_item(full_path, item, stop_event)
                    if child_structure:
                        batch_children.append(child_structure)
                except Exception as e:
                    logger.error(f"Error processing {item}: {e}")
        return batch_children

    def _process_item(
        self, full_path: str, item: str, stop_event: threading.Event
    ) -> Optional[Dict[str, Any]]:
        if os.path.isdir(full_path):
            child_structure = self._analyze_recursive(full_path, stop_event)
            if stop_event.is_set():
                return None
            return child_structure
        else:
            return self._process_file(full_path, item)

    @check_stop_event
    def _analyze_recursive(
        self, current_dir: str, stop_event: threading.Event
    ) -> Dict[str, Any]:
        try:
            if not os.path.exists(current_dir):
                return self._create_error_structure(
                    current_dir, "Directory does not exist"
                )

            if self.settings_manager.is_excluded(current_dir):
                logger.debug(f"Skipping excluded directory: {current_dir}")
                return {}

            if stop_event.is_set():
                return {}

            structure = self._create_base_structure(current_dir)

            try:
                items = os.listdir(current_dir)
                children = self._process_directory_items(items, current_dir, stop_event)
                if stop_event.is_set():
                    return {}
                structure["children"] = children

            except PermissionError as e:
                error_msg = f"Permission denied: {str(e)}"
                logger.warning(error_msg)
                structure["error"] = error_msg
            except Exception as e:
                error_msg = f"Error analyzing directory: {str(e)}"
                logger.error(error_msg)
                structure["error"] = error_msg

            return structure

        except Exception as e:
            logger.error(f"Error in recursive analysis: {e}")
            return self._create_error_structure(
                current_dir, f"Error analyzing directory: {str(e)}"
            )

    @check_stop_event
    def get_flat_structure(
        self, start_dir: str, stop_event: threading.Event
    ) -> List[Dict[str, Any]]:
        if not start_dir or not os.path.exists(start_dir):
            logger.error(f"Invalid directory path: {start_dir}")
            return []

        logger.debug(f"Generating flat structure for: {start_dir}")
        flat_structure: List[Dict[str, Any]] = []

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
                            flat_structure.append(
                                {
                                    "path": full_path,
                                    "type": "file",
                                    "description": description,
                                }
                            )
                    except Exception as e:
                        logger.warning(
                            f"Error processing file {file}: {e}", exc_info=True
                        )
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

    def _walk_directory(
        self, start_dir: str, stop_event: threading.Event
    ) -> Generator[tuple[str, List[str], List[str]], None, None]:
        if not os.path.exists(start_dir):
            logger.error(f"Directory does not exist: {start_dir}")
            return

        try:
            for root, dirs, files in os.walk(start_dir):
                if stop_event.is_set():
                    logger.debug("Directory walk stopped.")
                    return

                try:
                    if stop_event.is_set():
                        return
                    dirs[:] = [
                        d
                        for d in dirs
                        if not self.settings_manager.is_excluded(os.path.join(root, d))
                    ]
                    yield root, dirs, files
                except Exception as e:
                    logger.warning(
                        f"Error processing directory {root}: {e}", exc_info=True
                    )
                    continue
        except Exception as e:
            logger.error(f"Error walking directory structure: {e}", exc_info=True)
            return

    def _safe_get_file_purpose(self, file_path: str) -> Optional[str]:
        if not os.path.exists(file_path):
            return None

        try:
            result = self.comment_parser.get_file_purpose(file_path)
            return result if isinstance(result, str) else None
        except Exception as e:
            logger.warning(
                f"Error getting file purpose for {file_path}: {e}", exc_info=True
            )
            return None
