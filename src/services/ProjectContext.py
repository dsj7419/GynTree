import logging
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, TypedDict, Union, cast

from models.Project import Project
from services.auto_exclude.AutoExcludeManager import AutoExcludeManager
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.ProjectTypeDetector import ProjectTypeDetector
from services.RootExclusionManager import RootExclusionManager
from services.SettingsManager import SettingsManager
from utilities.error_handler import handle_exception

logger = logging.getLogger(__name__)


# Directory structure types
class FileNode(TypedDict):
    type: Literal["file"]
    path: str
    description: str
    name: str


class DirectoryNode(TypedDict):
    type: Literal["directory"]
    path: str
    name: str
    description: str
    children: List["TreeNode"]


TreeNode = Union[FileNode, DirectoryNode]


class ProjectContext:
    VALID_THEMES = {"light", "dark"}

    def __init__(self, project: Project) -> None:
        if not isinstance(project, Project):
            raise TypeError("Expected Project instance")
        self.project = project
        self.settings_manager: Optional[SettingsManager] = None
        self.directory_analyzer: Optional[DirectoryAnalyzer] = None
        self.auto_exclude_manager: Optional[AutoExcludeManager] = None
        self.root_exclusion_manager = RootExclusionManager()
        self.project_types: Set[str] = set()
        self.detected_types: Dict[str, bool] = {}
        self.project_type_detector: Optional[ProjectTypeDetector] = None
        self._is_active = False

    def initialize(self) -> bool:
        try:
            if self._is_active:
                logger.warning(
                    "Attempting to initialize already active project context"
                )
                return False

            if not self.project.start_directory:
                raise ValueError("Project start directory not specified")

            if not Path(self.project.start_directory).exists():
                self._is_active = False
                self.settings_manager = None
                raise ValueError("Project directory does not exist")

            logger.debug(f"Initializing project context for {self.project.name}")

            self.settings_manager = SettingsManager(self.project)
            self.project_type_detector = ProjectTypeDetector(
                self.project.start_directory
            )
            self.detect_project_types()

            if self.root_exclusion_manager and self.settings_manager:
                new_exclusions = self.root_exclusion_manager.get_root_exclusions(
                    self.detected_types, self.project.start_directory
                )
                current_exclusions = set(self.settings_manager.get_root_exclusions())
                all_exclusions = current_exclusions.union(new_exclusions)
                self.settings_manager.update_settings(
                    {"root_exclusions": list(all_exclusions)}
                )

            self.initialize_auto_exclude_manager()
            self.initialize_directory_analyzer()

            self._is_active = True
            logger.debug(
                f"Project context initialized successfully for {self.project.name}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ProjectContext: {str(e)}")
            self.close()
            raise

    def detect_project_types(self) -> None:
        if not self.project_type_detector:
            raise RuntimeError("ProjectTypeDetector not initialized")
        self.detected_types = self.project_type_detector.detect_project_types()
        self.project_types = {
            ptype for ptype, detected in self.detected_types.items() if detected
        }
        logger.debug(f"Detected project types: {self.project_types}")

    def initialize_root_exclusions(self) -> None:
        if not self.settings_manager:
            raise RuntimeError("SettingsManager not initialized")

        current_root_exclusions = set(self.settings_manager.get_root_exclusions())
        if not current_root_exclusions:
            current_root_exclusions = set(self.project.root_exclusions)

        if not self.root_exclusion_manager:
            return

        default_root_exclusions = self.root_exclusion_manager.get_root_exclusions(
            self.detected_types, self.project.start_directory
        )

        updated_root_exclusions = (
            self.root_exclusion_manager.merge_with_existing_exclusions(
                current_root_exclusions, default_root_exclusions
            )
        )

        if updated_root_exclusions != current_root_exclusions:
            logger.info(f"Updating root exclusions: {updated_root_exclusions}")
            self.settings_manager.update_settings(
                {"root_exclusions": list(updated_root_exclusions)}
            )

    def initialize_auto_exclude_manager(self) -> None:
        if not self.settings_manager or not self.project_type_detector:
            raise RuntimeError("Required components not initialized")

        self.auto_exclude_manager = AutoExcludeManager(
            self.project.start_directory,
            self.settings_manager,
            self.project_types,
            self.project_type_detector,
        )
        logger.debug("Initialized AutoExcludeManager")

    def initialize_directory_analyzer(self) -> None:
        if not self.settings_manager:
            raise RuntimeError("SettingsManager not initialized")

        if not Path(self.project.start_directory).exists():
            self._is_active = False
            self.settings_manager = None
            raise ValueError("Project directory does not exist")

        self.directory_analyzer = DirectoryAnalyzer(
            self.project.start_directory, self.settings_manager
        )
        logger.debug("Initialized DirectoryAnalyzer")

    @handle_exception
    def stop_analysis(self) -> None:
        if self.directory_analyzer:
            self.directory_analyzer.stop()

    def reinitialize_directory_analyzer(self) -> None:
        self.initialize_directory_analyzer()

    @handle_exception
    def trigger_auto_exclude(self) -> str:
        if not self._is_active:
            return "Project context not initialized"

        if not self.settings_manager:
            logger.error(
                "SettingsManager not initialized. Cannot perform auto-exclude."
            )
            return "Project context not initialized"

        if not self.auto_exclude_manager:
            logger.warning(
                "AutoExcludeManager not initialized. Attempting to reinitialize."
            )
            try:
                self.initialize_auto_exclude_manager()
                if not self.auto_exclude_manager:
                    return "Auto-exclude manager initialization failed"
            except Exception:
                return "Auto-exclude manager initialization failed"

        try:
            if not self.auto_exclude_manager:
                return "Auto-exclude manager not available"
            self.auto_exclude_manager.get_recommendations()  # Updates internal state
            formatted_recommendations: str = (
                self.auto_exclude_manager.get_formatted_recommendations()
            )
            return formatted_recommendations
        except Exception as e:
            error_msg = f"Error in auto-exclude process: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def get_directory_tree(self) -> DirectoryNode:
        if not self.directory_analyzer:
            raise RuntimeError("DirectoryAnalyzer not initialized")
        if not self.settings_manager:
            raise RuntimeError("SettingsManager not initialized")

        result = self.directory_analyzer.analyze_directory()
        if not isinstance(result, dict) or result.get("type") != "directory":
            raise RuntimeError("Invalid directory structure returned")

        return cast(DirectoryNode, result)

    def save_settings(self) -> None:
        if self.settings_manager:
            self.settings_manager.save_settings()

    def get_theme_preference(self) -> str:
        if not self.settings_manager:
            return "light"
        try:
            theme: str = cast(str, self.settings_manager.get_theme_preference())
            return theme if theme in self.VALID_THEMES else "light"
        except Exception:
            return "light"

    def set_theme_preference(self, theme: str) -> None:
        if theme not in self.VALID_THEMES:
            raise ValueError(
                f"Invalid theme. Must be one of: {', '.join(self.VALID_THEMES)}"
            )

        if not self.settings_manager:
            raise RuntimeError("SettingsManager not initialized")

        self.settings_manager.set_theme_preference(theme)
        self.save_settings()

    @property
    def is_initialized(self) -> bool:
        return (
            self._is_active
            and self.settings_manager is not None
            and self.directory_analyzer is not None
        )

    @handle_exception
    def close(self) -> None:
        logger.debug(f"Closing project context for project: {self.project.name}")
        try:
            self.stop_analysis()

            if self.settings_manager:
                self.settings_manager.save_settings()

            if self.directory_analyzer:
                self.directory_analyzer.stop()

            self.settings_manager = None
            self.directory_analyzer = None
            self.auto_exclude_manager = None
            self.project_types.clear()
            self.detected_types.clear()
            self.project_type_detector = None
            self._is_active = False

            logger.debug(f"Project context closed for project: {self.project.name}")
        except Exception as e:
            logger.error(f"Error during project context cleanup: {str(e)}")
            raise

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
