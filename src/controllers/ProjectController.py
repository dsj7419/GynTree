"""
GynTree: ProjectController manages loading, saving, setting projects.
This controller handles main project-related operations, ensuring current project properly set
and context established. Interacts with ProjectManager and ProjectContext services to
manage the lifecycle of a project within the application.

Responsibilities:
- Load and save projects via ProjectManager.
- Set current project and initialize project context.
- Handle project transitions and cleanup.
- Provide project-related information to main UI.
"""

import logging
from models.Project import Project
from services.ProjectManager import ProjectManager
from services.ProjectContext import ProjectContext

logger = logging.getLogger(__name__)

class ProjectController:
    def __init__(self, app_controller):
        self.app_controller = app_controller
        self.project_manager = ProjectManager()
        self.current_project = None
        self.project_context = None

    def create_project(self, project: Project) -> bool:
        try:
            self.project_manager.save_project(project)
            self._transition_to_project(project)
            return True
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            return False

    def load_project(self, project_name: str) -> Project:
        try:
            project = self.project_manager.load_project(project_name)
            if project:
                self._transition_to_project(project)
                return project
        except Exception as e:
            logger.error(f"Failed to load project: {str(e)}")
        return None

    def _transition_to_project(self, project: Project):
        """Handle the transition from current project to new project"""
        try:
            # Clean up existing project if it exists
            if self.project_context:
                logger.debug(f"Cleaning up existing project: {self.current_project.name}")
                self._cleanup_current_project()

            # Initialize new project context
            logger.debug(f"Transitioning to project: {project.name}")
            self.project_context = ProjectContext(project)
            self.current_project = project
            
            # Initialize new project resources
            self._initialize_project_resources()
            
            logger.debug(f"Project '{project.name}' set as active.")
        except Exception as e:
            logger.error(f"Failed to transition to project: {str(e)}")
            raise

    def _cleanup_current_project(self):
        """Clean up resources for current project"""
        try:
            if self.project_context:
                # Save current project state
                self.project_context.save_settings()
                
                # Clean up project context
                self.project_context.close()
                
                # Clean up UI components
                self.app_controller.ui_controller.reset_ui()
                
                self.project_context = None
                self.current_project = None
                
                logger.debug("Project cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during project cleanup: {str(e)}")
            raise

    def _initialize_project_resources(self):
        """Initialize resources for new project"""
        try:
            if self.project_context:
                # Initialize project analysis
                self.project_context.initialize()
                
                # Update UI with new project
                self.app_controller.ui_controller.update_project_info(self.current_project)
                
                logger.debug("Project resources initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing project resources: {str(e)}")
            raise

    def get_theme_preference(self):
        return self.project_context.get_theme_preference() if self.project_context else 'light'

    def set_theme_preference(self, theme: str):
        if self.project_context:
            self.project_context.set_theme_preference(theme)

    def analyze_directory(self):
        """Trigger directory analysis"""
        if self.project_context:
            result_ui = self.app_controller.ui_controller.show_result(
                self.project_context.directory_analyzer)
            result_ui.update_result()
        else:
            logger.error("Cannot analyze directory: project_context is None.")

    def view_directory_tree(self):
        """Trigger view directory structure"""
        if self.project_context:
            result = self.project_context.get_directory_tree()
            self.app_controller.ui_controller.view_directory_tree(result)
        else:
            logger.error("Cannot view directory tree: project_context is None.")