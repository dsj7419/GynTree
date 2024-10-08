import logging
import traceback
from models.Project import Project
from services.SettingsManager import SettingsManager
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.auto_exclude.AutoExcludeManager import AutoExcludeManager
from services.RootExclusionManager import RootExclusionManager
from services.ProjectTypeDetector import ProjectTypeDetector
from utilities.error_handler import handle_exception

logger = logging.getLogger(__name__)

class ProjectContext:
    def __init__(self, project: Project):
        self.project = project
        self.settings_manager = None
        self.directory_analyzer = None
        self.auto_exclude_manager = None
        self.root_exclusion_manager = RootExclusionManager()
        self.project_types = set()
        self.detected_types = {}
        self.project_type_detector = None
        self.initialize()

    @handle_exception
    def initialize(self):
        try:
            self.settings_manager = SettingsManager(self.project)
            self.project_type_detector = ProjectTypeDetector(self.project.start_directory)
            self.detect_project_types()
            self.initialize_root_exclusions()
            self.initialize_auto_exclude_manager()
            self.initialize_directory_analyzer()
            self.settings_manager.save_settings()
        except Exception as e:
            logger.error(f"Failed to initialize ProjectContext: {str(e)}")
            raise

    def detect_project_types(self):
        self.detected_types = self.project_type_detector.detect_project_types()
        self.project_types = {ptype for ptype, detected in self.detected_types.items() if detected}
        logger.debug(f"Detected project types: {self.project_types}")

    def initialize_root_exclusions(self):
        default_root_exclusions = self.root_exclusion_manager.get_root_exclusions(
            self.detected_types, self.project.start_directory
        )
        current_root_exclusions = set(self.settings_manager.get_root_exclusions())
        updated_root_exclusions = self.root_exclusion_manager.merge_with_existing_exclusions(
            current_root_exclusions, default_root_exclusions
        )
        if updated_root_exclusions != current_root_exclusions:
            logger.info(f"Updating root exclusions: {updated_root_exclusions}")
            self.settings_manager.update_settings({'root_exclusions': list(updated_root_exclusions)})

    def initialize_auto_exclude_manager(self):
        try:
            if not self.auto_exclude_manager:
                self.auto_exclude_manager = AutoExcludeManager(
                    self.project.start_directory,
                    self.settings_manager,
                    self.project_types,
                    self.project_type_detector
                )
                logger.debug("Initialized AutoExcludeManager")
        except Exception as e:
            logger.error(f"Failed to initialize AutoExcludeManager: {str(e)}")
            self.auto_exclude_manager = None

    def initialize_directory_analyzer(self):
        self.directory_analyzer = DirectoryAnalyzer(
            self.project.start_directory,
            self.settings_manager
        )
        logger.debug("Initialized DirectoryAnalyzer")

    @handle_exception
    def stop_analysis(self):
        if self.directory_analyzer:
            self.directory_analyzer.stop()

    def reinitialize_directory_analyzer(self):
        self.initialize_directory_analyzer()

    @handle_exception
    def trigger_auto_exclude(self) -> str:
        if not self.auto_exclude_manager:
            logger.warning("AutoExcludeManager not initialized. Attempting to reinitialize.")
            self.initialize_auto_exclude_manager()

        if not self.auto_exclude_manager:
            logger.error("Failed to initialize AutoExcludeManager. Cannot perform auto-exclude.")
            return "Auto-exclude manager initialization failed."

        if not self.settings_manager:
            logger.error("SettingsManager not initialized. Cannot perform auto-exclude.")
            return "Settings manager missing."

        try:
            new_recommendations = self.auto_exclude_manager.get_recommendations()
            return self.auto_exclude_manager.get_formatted_recommendations()
        except Exception as e:
            logger.error(f"Failed to trigger auto-exclude: {str(e)}")
            return "Error during auto-exclude process."

    def get_directory_tree(self):
        return self.directory_analyzer.analyze_directory()

    def save_settings(self):
        if self.settings_manager:
            self.settings_manager.save_settings()

    def get_theme_preference(self) -> str:
        return self.settings_manager.get_theme_preference() if self.settings_manager else 'light'

    def set_theme_preference(self, theme: str):
        if self.settings_manager:
            self.settings_manager.set_theme_preference(theme)
        self.save_settings()

    @property
    def is_initialized(self) -> bool:
        return self.settings_manager is not None and self.directory_analyzer is not None

    @handle_exception
    def close(self):
        logger.debug(f"Closing project context for project: {self.project.name}")
        self.stop_analysis()
        if self.settings_manager:
            self.settings_manager.save_settings()
            self.settings_manager = None
        if self.directory_analyzer:
            self.directory_analyzer.stop()
            self.directory_analyzer = None
        if self.auto_exclude_manager:
            self.auto_exclude_manager = None
        self.project_types.clear()
        self.detected_types.clear()
        self.project_type_detector = None
        logger.debug(f"Project context closed for project: {self.project.name}")

    def __del__(self):
        self.close()