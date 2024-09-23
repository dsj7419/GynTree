import logging
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox, QApplication
from components.UI.DashboardUI import DashboardUI
from controllers.ProjectController import ProjectController
from controllers.ThreadController import ThreadController
from controllers.UIController import UIController
from utilities.error_handler import handle_exception
from utilities.logging_decorator import log_method
from utilities.theme_manager import ThemeManager

logger = logging.getLogger(__name__)

class AppController(QObject):
    project_created = pyqtSignal(object)
    project_loaded = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.main_ui = DashboardUI(self)
        self.theme_manager = ThemeManager.getInstance()
        self.project_controller = ProjectController(self)
        self.thread_controller = ThreadController()
        self.ui_controller = UIController(self.main_ui)
        self.ui_components = []
        self.project_context = None

        self.thread_controller.worker_finished.connect(self._on_auto_exclude_finished)
        self.thread_controller.worker_error.connect(self._on_auto_exclude_error)

        self.theme_manager.themeChanged.connect(self.apply_theme_to_all_windows)

        initial_theme = self.get_theme_preference()
        self.theme_manager.set_theme(initial_theme)

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
        
        self.thread_controller.cleanup_thread()
        
        if self.project_controller and self.project_controller.project_context:
            self.project_controller.project_context.close()
        
        for ui in self.ui_components:
            if ui and not ui.isHidden():
                logger.debug(f"Closing UI: {type(ui).__name__}")
                ui.close()
                ui.deleteLater()
        
        self.ui_components.clear()

        QApplication.closeAllWindows()

        logger.debug("Cleanup process in AppController completed")

    def toggle_theme(self):
        new_theme = self.theme_manager.toggle_theme()
        self.set_theme_preference(new_theme)

    def apply_theme_to_all_windows(self, theme):
        app = QApplication.instance()
        self.theme_manager.apply_theme_to_all_windows(app)

    def get_theme_preference(self):
        return self.project_controller.get_theme_preference() if self.project_controller else 'light'

    def set_theme_preference(self, theme):
        if self.project_controller:
            self.project_controller.set_theme_preference(theme)

    @handle_exception
    @log_method
    def create_project_action(self, *args):
        logger.debug("Creating project UI")
        project_ui = self.main_ui.show_project_ui()
        project_ui.project_created.connect(self.on_project_created)
        self.ui_components.append(project_ui)

    @handle_exception
    @log_method
    def on_project_created(self, project):
        logger.info(f"Project created signal received for project: {project.name}")
        try:
            success = self.project_controller.create_project(project)
            if success:
                logger.info(f"Project {project.name} created successfully")
                self.project_context = self.project_controller.project_context
                self.project_created.emit(project)
                self.main_ui.update_project_info(project)  # Call this only once
                self.after_project_loaded()
            else:
                logger.error(f"Failed to create project: {project.name}")
                QMessageBox.critical(self.main_ui, "Error", "Failed to create project. Please try again.")
        except Exception as e:
            logger.exception(f"Exception occurred while creating project: {str(e)}")
            QMessageBox.critical(self.main_ui, "Error", f"An unexpected error occurred: {str(e)}")

    @handle_exception
    @log_method
    def load_project_action(self, *args):
        logger.debug("Loading project UI")
        project_ui = self.main_ui.show_project_ui()
        project_ui.project_loaded.connect(self.on_project_loaded)
        self.ui_components.append(project_ui)

    @handle_exception
    @log_method
    def on_project_loaded(self, project):
        loaded_project = self.project_controller.load_project(project.name)
        if loaded_project:
            self.project_loaded.emit(loaded_project)
            self.main_ui.update_project_info(loaded_project)  # Call this only once
            self.after_project_loaded()
        else:
            QMessageBox.critical(self.main_ui, "Error", "Failed to load project. Please try again.")

    @handle_exception
    @log_method
    def after_project_loaded(self):
        self.ui_controller.reset_ui()
        if self.project_controller and self.project_controller.project_context:
            self._start_auto_exclude()
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
        if self.project_controller and self.project_controller.project_context:
            exclusions_manager_ui = self.ui_controller.manage_exclusions(self.project_controller.project_context.settings_manager)
            self.ui_components.append(exclusions_manager_ui)
        else:
            logger.error("No project context available.")
            QMessageBox.warning(self.main_ui, "Error", "No project is currently loaded. Please load a project first.")

    @handle_exception
    @log_method
    def view_directory_tree(self, *args):
        if self.project_controller and self.project_controller.project_context:
            result = self.project_controller.project_context.get_directory_tree()
            directory_tree_ui = self.ui_controller.view_directory_tree(result)
            self.ui_components.append(directory_tree_ui)
        else:
            logger.error("Cannot view directory tree: project_context is None.")
            QMessageBox.warning(self.main_ui, "Error", "No project is currently loaded. Please load a project first.")

    @handle_exception
    @log_method
    def analyze_directory(self, *args):
        if self.project_controller and self.project_controller.project_context:
            result_ui = self.ui_controller.show_result(self.project_controller.project_context.directory_analyzer)
            if result_ui is not None:
                result_ui.update_result()
            else:
                logger.error("ResultUI could not be initialized.")
        else:
            logger.error("Cannot analyze directory: project_context is None.")
            QMessageBox.warning(self.main_ui, "Error", "No project is currently loaded. Please load a project first.")

    def __del__(self):
        logger.debug("AppController destructor called")
        self.cleanup()