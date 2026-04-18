import logging
from typing import Any, Dict, Optional

from models.Project import Project
from services.ProjectContext import ProjectContext
from services.ProjectManager import ProjectManager
from utilities.error_handler import handle_exception
from utilities.logging_decorator import log_method

logger = logging.getLogger(__name__)


class ProjectController:
    def __init__(self, app_controller: Any) -> None:
        self.app_controller = app_controller
        self.project_manager = ProjectManager()
        self.current_project: Optional[Project] = None
        self.project_context: Optional[ProjectContext] = None

    @handle_exception
    @log_method
    def create_project(self, project: Project) -> bool:
        try:
            logger.info(f"Creating new project: {project.name}")
            self._transition_to_project(project)
            self.project_manager.save_project(project)
            return True
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            self._cleanup_current_project()
            raise

    @handle_exception
    @log_method
    def load_project(self, project_name: str) -> Optional[Project]:
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
        try:
            if self.project_context and self.current_project:
                logger.debug(f"Cleaning existing project: {self.current_project.name}")
                self._cleanup_current_project()

            logger.debug(f"Creating new project context for: {project.name}")
            self.project_context = ProjectContext(project)
            self.current_project = project

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
        try:
            if self.project_context and self.current_project:
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
            self.project_context = None
            self.current_project = None
            raise

    @handle_exception
    @log_method
    def get_theme_preference(self) -> str:
        if self.project_context:
            theme: str = self.project_context.get_theme_preference()
            return theme
        return "light"

    @handle_exception
    @log_method
    def set_theme_preference(self, theme: str) -> None:
        if self.project_context:
            self.project_context.set_theme_preference(theme)

    @handle_exception
    @log_method
    def analyze_directory(self) -> None:
        if self.project_context:
            result_ui = self.app_controller.ui_controller.show_result(
                self.project_context.directory_analyzer
            )
            if result_ui is not None:
                result_ui.update_result()
        else:
            logger.error("Cannot analyze directory: project_context is None.")

    @handle_exception
    @log_method
    def view_directory_tree(self) -> None:
        if self.project_context:
            result = self.project_context.get_directory_tree()
            self.app_controller.ui_controller.view_directory_tree(result)
        else:
            logger.error("Cannot view directory tree: project_context is None.")

    @property
    def is_project_loaded(self) -> bool:
        return (
            self.current_project is not None
            and self.project_context is not None
            and self.project_context.is_initialized
        )

    def get_project_info(self) -> Dict[str, Any]:
        if (
            not self.is_project_loaded
            or not self.current_project
            or not self.project_context
        ):
            return {}

        return {
            "name": self.current_project.name,
            "start_directory": self.current_project.start_directory,
            "is_initialized": self.project_context.is_initialized,
            "project_types": list(self.project_context.project_types),
            "theme": self.project_context.get_theme_preference(),
        }
