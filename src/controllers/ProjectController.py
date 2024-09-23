"""
GynTree: ProjectController manages the loading, saving, and setting of projects.
This controller handles the main project-related operations, ensuring that the
current project is properly set up and context is established. It interacts with
the ProjectManager and ProjectContext services to manage the lifecycle of the
project within the application.

Responsibilities:
- Load and save projects from the ProjectManager.
- Set the current project and initialize project context.
- Provide project-related information to the main UI.
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
            self._set_current_project(project)
            return True
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}")
            return False

    def load_project(self, project_name: str) -> Project:
        try:
            project = self.project_manager.load_project(project_name)
            if project:
                self._set_current_project(project)
            return project
        except Exception as e:
            logger.error(f"Failed to load project: {str(e)}")
            return None

    def _set_current_project(self, project: Project):
        if self.project_context:
            self.project_context.close()
        self.project_context = ProjectContext(project)
        self.current_project = project
        logger.debug(f"Project '{project.name}' set as active.")

    def get_theme_preference(self):
        return self.project_context.get_theme_preference() if self.project_context else 'light'

    def set_theme_preference(self, theme: str):
        if self.project_context:
            self.project_context.set_theme_preference(theme)

    def analyze_directory(self):
        """Trigger directory analysis"""
        if self.project_context:
            result_ui = self.app_controller.ui_controller.show_result(self.project_context.directory_analyzer)
            result_ui.update_result()
        else:
            logger.error("Cannot analyze directory: project_context is None.")

    def view_directory_tree(self):
        """Trigger view of the directory structure"""
        if self.project_context:
            result = self.project_context.get_directory_tree()
            self.app_controller.ui_controller.view_directory_tree(result)
        else:
            logger.error("Cannot view directory tree: project_context is None.")
