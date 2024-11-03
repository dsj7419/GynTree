"""
GynTree: ProjectController manages loading, saving, and setting of projects.
This controller handles the main project-related operations, ensuring the current project
is properly set and its context established. It interacts with ProjectManager and ProjectContext
services to manage the lifecycle of a project within the application.

Responsibilities:
- Load and save projects via ProjectManager
- Set current project and initialize project context
- Handle project transitions and cleanup
- Provide project-related information to main UI
- Manage project settings and preferences
"""

import logging
from typing import Any, Dict, Optional

from models.Project import Project
from services.ProjectContext import ProjectContext
from services.ProjectManager import ProjectManager
from utilities.error_handler import handle_exception
from utilities.logging_decorator import log_method

logger = logging.getLogger(__name__)


class ProjectController:
    """
    Controls project-related operations and maintains project state.

    This controller is responsible for managing the lifecycle of projects,
    including loading, saving, and transitioning between projects. It ensures
    proper initialization and cleanup of project resources.

    Attributes:
        app_controller: Reference to the main application controller
        project_manager: Handles project persistence operations
        current_project: Currently active project instance
        project_context: Context containing project-specific services and state
    """

    def __init__(self, app_controller):
        """
        Initialize ProjectController with necessary dependencies.

        Args:
            app_controller: Reference to the main application controller
        """
        self.app_controller = app_controller
        self.project_manager = ProjectManager()
        self.current_project: Optional[Project] = None
        self.project_context: Optional[ProjectContext] = None

    @handle_exception
    @log_method
    def create_project(self, project: Project) -> bool:
        """
        Create a new project and initialize its context.

        Args:
            project: Project instance to create

        Returns:
            bool: True if project was created successfully, False otherwise

        Raises:
            Exception: If project creation or initialization fails
        """
        try:
            logger.info(f"Creating new project: {project.name}")
            self.project_manager.save_project(project)
            self._transition_to_project(project)
            return True
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            # Clean up any partially created resources
            self._cleanup_current_project()
            raise

    @handle_exception
    @log_method
    def load_project(self, project_name: str) -> Optional[Project]:
        """
        Load an existing project and initialize its context.

        Args:
            project_name: Name of the project to load

        Returns:
            Project instance if successfully loaded, None otherwise

        Raises:
            Exception: If project loading or initialization fails
        """
        try:
            logger.debug(f"Loading project: {project_name}")
            loaded_project = self.project_manager.load_project(project_name)

            if loaded_project:
                logger.debug(
                    f"Project data loaded, transitioning to project: {loaded_project.name}"
                )
                self._transition_to_project(loaded_project)
                return loaded_project

            logger.error(f"Failed to load project data for: {project_name}")
            return None

        except Exception as e:
            logger.error(f"Error loading project {project_name}: {str(e)}")
            self._cleanup_current_project()
            raise

    @handle_exception
    @log_method
    def _transition_to_project(self, project: Project) -> None:
        """
        Handle transition to a new project with proper cleanup and initialization.

        Args:
            project: Project to transition to

        Raises:
            RuntimeError: If project context initialization fails
            Exception: For other initialization failures
        """
        try:
            # Clean up existing project if there is one
            if self.project_context:
                logger.debug(f"Cleaning existing project: {self.current_project.name}")
                self._cleanup_current_project()

            # Initialize new project context
            logger.debug(f"Creating new project context for: {project.name}")
            self.project_context = ProjectContext(project)
            self.current_project = project

            # Initialize the new project's resources
            logger.debug(f"Initializing resources for project: {project.name}")
            if not self.project_context.initialize():
                raise RuntimeError(
                    f"Failed to initialize project context for {project.name}"
                )

            logger.info(f"Successfully transitioned to project: {project.name}")

        except Exception as e:
            logger.error(f"Failed to transition to project {project.name}: {str(e)}")
            self._cleanup_current_project()
            raise

    @handle_exception
    @log_method
    def _cleanup_current_project(self) -> None:
        """
        Clean up resources for the current project.

        This method ensures proper cleanup of all project-related resources,
        including saving current state and cleaning up UI components.
        """
        try:
            if self.project_context:
                logger.debug(
                    f"Starting cleanup for project: {self.current_project.name}"
                )
                try:
                    self.project_context.save_settings()
                except Exception as e:
                    logger.warning(
                        f"Non-critical error saving project settings: {str(e)}"
                    )

                try:
                    self.project_context.close()
                except Exception as e:
                    logger.warning(
                        f"Non-critical error closing project context: {str(e)}"
                    )

            if self.app_controller.ui_controller:
                try:
                    self.app_controller.ui_controller.reset_ui()
                except Exception as e:
                    logger.warning(f"Non-critical error resetting UI: {str(e)}")

            self.project_context = None
            self.current_project = None
            logger.debug("Project cleanup completed successfully")

        except Exception as e:
            logger.error(f"Error during project cleanup: {str(e)}")
            # Ensure state is reset even if cleanup fails
            self.project_context = None
            self.current_project = None
            raise

    @handle_exception
    @log_method
    def get_theme_preference(self) -> str:
        """
        Get the current theme preference.

        Returns:
            str: Current theme preference ('light' or 'dark')
        """
        if self.project_context:
            return self.project_context.get_theme_preference()
        return "light"

    @handle_exception
    @log_method
    def set_theme_preference(self, theme: str) -> None:
        """
        Set the theme preference and save settings.

        Args:
            theme: Theme to set ('light' or 'dark')
        """
        if self.project_context:
            self.project_context.set_theme_preference(theme)

    @handle_exception
    @log_method
    def analyze_directory(self) -> None:
        """
        Trigger directory analysis for the current project.
        """
        if self.project_context:
            result_ui = self.app_controller.ui_controller.show_result(
                self.project_context.directory_analyzer
            )
            result_ui.update_result()
        else:
            logger.error("Cannot analyze directory: project_context is None.")

    @handle_exception
    @log_method
    def view_directory_tree(self) -> None:
        """
        Trigger view of directory structure for the current project.
        """
        if self.project_context:
            result = self.project_context.get_directory_tree()
            self.app_controller.ui_controller.view_directory_tree(result)
        else:
            logger.error("Cannot view directory tree: project_context is None.")

    @property
    def is_project_loaded(self) -> bool:
        """
        Check if a project is currently loaded and initialized.

        Returns:
            bool: True if a project is loaded and initialized, False otherwise
        """
        return (
            self.current_project is not None
            and self.project_context is not None
            and self.project_context.is_initialized
        )

    def get_project_info(self) -> Dict[str, Any]:
        """
        Get information about the current project.

        Returns:
            Dict containing project information or empty dict if no project loaded
        """
        if not self.is_project_loaded:
            return {}

        return {
            "name": self.current_project.name,
            "start_directory": self.current_project.start_directory,
            "is_initialized": self.project_context.is_initialized,
            "project_types": list(self.project_context.project_types),
            "theme": self.project_context.get_theme_preference(),
        }
