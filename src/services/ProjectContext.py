import logging
import traceback
from pathlib import Path
from models.Project import Project
from services.SettingsManager import SettingsManager
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.auto_exclude.AutoExcludeManager import AutoExcludeManager
from services.RootExclusionManager import RootExclusionManager
from services.ProjectTypeDetector import ProjectTypeDetector
from utilities.error_handler import handle_exception

logger = logging.getLogger(__name__)

class ProjectContext:
    VALID_THEMES = {'light', 'dark'}

    def __init__(self, project: Project):
        if not isinstance(project, Project):
            raise TypeError("Expected Project instance")
        self.project = project
        self.settings_manager = None
        self.directory_analyzer = None
        self.auto_exclude_manager = None
        self.root_exclusion_manager = RootExclusionManager()
        self.project_types = set()
        self.detected_types = {}
        self.project_type_detector = None
        self._is_active = False

    def initialize(self):
        """Initialize project context and resources"""
        try:
            if self._is_active:
                logger.warning("Attempting to initialize already active project context")
                return False

            if not self.project.start_directory:
                raise ValueError("Project start directory not specified")

            if not Path(self.project.start_directory).exists():
                self._is_active = False
                self.settings_manager = None
                raise ValueError("Project directory does not exist")

            logger.debug(f"Initializing project context for {self.project.name}")
            self.settings_manager = SettingsManager(self.project)
            self.project_type_detector = ProjectTypeDetector(self.project.start_directory)
            
            self.detect_project_types()
            self.initialize_root_exclusions()
            self.initialize_auto_exclude_manager()
            self.initialize_directory_analyzer()
            
            self._is_active = True
            self.settings_manager.save_settings()
            
            logger.debug(f"Project context initialized successfully for {self.project.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ProjectContext: {str(e)}")
            self.close()
            raise

    def detect_project_types(self):
        """Detect and set project types"""
        if not self.project_type_detector:
            raise RuntimeError("ProjectTypeDetector not initialized")
        self.detected_types = self.project_type_detector.detect_project_types()
        self.project_types = {
            ptype for ptype, detected in self.detected_types.items() if detected
        }
        logger.debug(f"Detected project types: {self.project_types}")

    def initialize_root_exclusions(self):
        """Initialize and update root exclusions"""
        if not self.settings_manager:
            raise RuntimeError("SettingsManager not initialized")
            
        default_root_exclusions = self.root_exclusion_manager.get_root_exclusions(
            self.detected_types,
            self.project.start_directory
        )
        
        current_root_exclusions = set(self.settings_manager.get_root_exclusions())
        if not current_root_exclusions:
            current_root_exclusions = set(self.project.root_exclusions)
        
        updated_root_exclusions = self.root_exclusion_manager.merge_with_existing_exclusions(
            current_root_exclusions,
            default_root_exclusions
        )
        
        if updated_root_exclusions != current_root_exclusions:
            logger.info(f"Updating root exclusions: {updated_root_exclusions}")
            self.settings_manager.update_settings({'root_exclusions': list(updated_root_exclusions)})

    def initialize_auto_exclude_manager(self):
        """Initialize auto-exclude manager"""
        try:
            if not self.settings_manager:
                raise RuntimeError("SettingsManager not initialized")
                
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
            raise

    def initialize_directory_analyzer(self):
        """Initialize directory analyzer"""
        try:
            if not self.settings_manager:
                raise RuntimeError("SettingsManager not initialized")
                
            if not Path(self.project.start_directory).exists():
                self._is_active = False
                self.settings_manager = None
                raise ValueError("Project directory does not exist")
                
            self.directory_analyzer = DirectoryAnalyzer(
                self.project.start_directory,
                self.settings_manager
            )
            logger.debug("Initialized DirectoryAnalyzer")
        except Exception as e:
            self._is_active = False
            self.settings_manager = None
            raise

    @handle_exception
    def stop_analysis(self):
        """Stop ongoing analysis operations"""
        if self.directory_analyzer:
            self.directory_analyzer.stop()

    def reinitialize_directory_analyzer(self):
        """Reinitialize directory analyzer"""
        try:
            self.initialize_directory_analyzer()
        except ValueError as e:
            self._is_active = False
            self.settings_manager = None
            self.directory_analyzer = None
            raise

    @handle_exception
    def trigger_auto_exclude(self) -> str:
        """Trigger auto-exclude analysis"""
        if not self._is_active:
            return "Project context not initialized"
            
        if not self.settings_manager:
            logger.error("SettingsManager not initialized. Cannot perform auto-exclude.")
            return "Project context not initialized"
            
        if not self.auto_exclude_manager:
            logger.warning("AutoExcludeManager not initialized. Attempting to reinitialize.")
            try:
                self.initialize_auto_exclude_manager()
            except Exception:
                return "Auto-exclude manager initialization failed"
            
        try:
            self.auto_exclude_manager.get_recommendations()
            return self.auto_exclude_manager.get_formatted_recommendations()
        except Exception as e:
            logger.error(f"Failed to trigger auto-exclude: {str(e)}")
            return f"Error in auto-exclude process: {str(e)}"

    def get_directory_tree(self):
        """Get directory tree structure"""
        if not self.directory_analyzer:
            raise RuntimeError("DirectoryAnalyzer not initialized")
        if not self.settings_manager:
            raise RuntimeError("SettingsManager not initialized")
            
        self.settings_manager.excluded_dirs = []
        return self.directory_analyzer.analyze_directory()

    def save_settings(self):
        """Save current settings"""
        if self.settings_manager:
            self.settings_manager.save_settings()

    def get_theme_preference(self) -> str:
        """Get theme preference"""
        if not self.settings_manager:
            return 'light'
        try:
            return self.settings_manager.get_theme_preference()
        except:
            return 'light' 

    def set_theme_preference(self, theme: str):
        """Set theme preference"""
        if theme not in self.VALID_THEMES:
            raise ValueError(f"Invalid theme. Must be one of: {', '.join(self.VALID_THEMES)}")
            
        if not self.settings_manager:
            raise RuntimeError("SettingsManager not initialized")
            
        self.settings_manager.set_theme_preference(theme)
        self.save_settings()

    @property
    def is_initialized(self) -> bool:
        """Check if context is properly initialized"""
        return (self._is_active and 
                self.settings_manager is not None and 
                self.directory_analyzer is not None)

    @handle_exception
    def close(self):
        """Close and cleanup project context"""
        logger.debug(f"Closing project context for project: {self.project.name}")
        try:
            self.stop_analysis()
            
            if self.settings_manager:
                self.settings_manager.save_settings()
                self.settings_manager = None
                
            self.directory_analyzer = None  # Moved before stop() call to ensure cleanup
            if self.directory_analyzer:
                self.directory_analyzer.stop()
                
            if self.auto_exclude_manager:
                self.auto_exclude_manager = None
                
            self.project_types.clear()
            self.detected_types.clear()
            self.project_type_detector = None
            self._is_active = False
            
            logger.debug(f"Project context closed for project: {self.project.name}")
        except Exception as e:
            logger.error(f"Error during project context cleanup: {str(e)}")
            raise

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.close()
        except:
            pass