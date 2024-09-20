"""
GynTree: AppController orchestrates the overall application workflow.
This controller ties together the other controllers (ProjectController, ThreadController,
UIController) to ensure smooth interaction between project management, thread handling,
and user interface updates. It acts as the main coordinator for the application.

Responsibilities:
- Delegate tasks to specialized controllers (project, thread, UI).
- Handle project creation and loading.
- Manage the overall application lifecycle, including cleanup.
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox
from components.UI.DashboardUI import DashboardUI
from controllers.ProjectController import ProjectController
from controllers.ThreadController import ThreadController
from controllers.UIController import UIController
from utilities.error_handler import handle_exception
from utilities.logging_decorator import log_method

logger = logging.getLogger(__name__)

class AppController(QObject):
    project_created = pyqtSignal(object)
    project_loaded = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.main_ui = DashboardUI(self)
        self.project_controller = ProjectController(self)
        self.thread_controller = ThreadController()
        self.ui_controller = UIController(self.main_ui)
        self.ui_components = []

        # Connect thread controller signals
        self.thread_controller.worker_finished.connect(self._on_auto_exclude_finished)
        self.thread_controller.worker_error.connect(self._on_auto_exclude_error)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False

    @log_method
    def run(self):
        self.main_ui.show_dashboard()

    @handle_exception
    @log_method
    def cleanup(self):
        logger.debug("Starting cleanup process in AppController")
        
        # Clean up thread controller
        self.thread_controller.cleanup_thread()
        
        # Close project context
        if self.project_controller and self.project_controller.project_context:
            self.project_controller.project_context.close()
        
        # Clean up UI components
        for ui in self.ui_components:
            if ui and not ui.isHidden():
                logger.debug(f"Closing UI: {type(ui).__name__}")
                ui.close()
                ui.deleteLater()
        
        self.ui_components.clear()
        logger.debug("Cleanup process in AppController completed")

    @handle_exception
    @log_method
    def create_project_action(self, *args):
        project_ui = self.main_ui.show_project_ui()
        project_ui.project_created.connect(self.on_project_created)
        self.ui_components.append(project_ui)

    @handle_exception
    @log_method
    def on_project_created(self, project):
        success = self.project_controller.create_project(project)
        if success:
            self.project_created.emit(project)
            self.main_ui.update_project_info(project)
            self.after_project_loaded()
        else:
            QMessageBox.critical(self.main_ui, "Error", "Failed to create project. Please try again.")

    @handle_exception
    @log_method
    def load_project_action(self, *args):
        project_ui = self.main_ui.show_project_ui()
        project_ui.project_loaded.connect(self.on_project_loaded)
        self.ui_components.append(project_ui)

    @handle_exception
    @log_method
    def on_project_loaded(self, project):
        loaded_project = self.project_controller.load_project(project.name)
        if loaded_project:
            self.project_loaded.emit(loaded_project)
            self.main_ui.update_project_info(loaded_project)
            self.after_project_loaded()
        else:
            QMessageBox.critical(self.main_ui, "Error", "Failed to load project. Please try again.")

    @handle_exception
    @log_method
    def after_project_loaded(self):
        self.ui_controller.reset_ui()
        if self.project_controller.project_context:
            QTimer.singleShot(0, self._start_auto_exclude)
        else:
            logger.error("Project context not initialized. Cannot start auto-exclude thread.")
            QMessageBox.warning(self.main_ui, "Warning", "Failed to initialize project context. Some features may not work correctly.")

    @handle_exception
    @log_method
    def _start_auto_exclude(self):
        self.thread_controller.start_auto_exclude_thread(self.project_controller.project_context)

    @handle_exception
    @log_method
    def _on_auto_exclude_finished(self, formatted_recommendations):
        if formatted_recommendations:
            auto_exclude_ui = self.main_ui.show_auto_exclude_ui(
                self.project_controller.project_context.auto_exclude_manager,
                self.project_controller.project_context.settings_manager,
                formatted_recommendations,
                self.project_controller.project_context
            )
            self.ui_components.append(auto_exclude_ui)
        else:
            logger.info("No new exclusions suggested.")
        self.main_ui.show_dashboard()

    @handle_exception
    @log_method
    def _on_auto_exclude_error(self, error_msg):
        logger.error(f"Auto-exclude error: {error_msg}")
        QMessageBox.critical(self.main_ui, "Error", f"An error occurred during auto-exclusion:\n{error_msg}")
        self.main_ui.show_dashboard()

    @handle_exception
    @log_method
    def manage_exclusions(self, *args):
        if self.project_controller.project_context:
            exclusions_manager_ui = self.ui_controller.manage_exclusions(self.project_controller.project_context.settings_manager)
            self.ui_components.append(exclusions_manager_ui)
        else:
            logger.error("No project context available.")

    @handle_exception
    @log_method
    def view_directory_tree(self, *args):
        if self.project_controller.project_context:
            result = self.project_controller.project_context.get_directory_tree()
            directory_tree_ui = self.ui_controller.view_directory_tree(result)
            self.ui_components.append(directory_tree_ui)
        else:
            logger.error("Cannot view directory tree: project_context is None.")

    @handle_exception
    @log_method
    def analyze_directory(self, *args):
        if self.project_controller.project_context:
            result_ui = self.ui_controller.show_result(self.project_controller.project_context.directory_analyzer)
            result_ui.update_result()
            self.ui_components.append(result_ui)
        else:
            logger.error("Cannot analyze directory: project_context is None.")

    def __del__(self):
        logger.debug("AppController destructor called")
        self.cleanup()