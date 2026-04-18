import logging
import logging.handlers
import threading
from typing import Any, List, Optional

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMessageBox, QWidget
from typing_extensions import Literal

from components.UI.DashboardUI import DashboardUI
from components.UI.ProjectUI import ProjectUI
from controllers.ProjectController import ProjectController
from controllers.ThreadController import ThreadController
from controllers.UIController import UIController
from models.Project import Project
from services.ProjectContext import ProjectContext
from utilities.error_handler import handle_exception
from utilities.logging_decorator import log_method
from utilities.theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class AppController(QObject):
    project_created = pyqtSignal(object)  # Project object
    project_loaded = pyqtSignal(object)  # Project object

    def __init__(self) -> None:
        super().__init__()
        self.main_ui: DashboardUI = DashboardUI(self)
        self.theme_manager: ThemeManager = ThemeManager.getInstance()
        self.project_controller: ProjectController = ProjectController(self)
        self.thread_controller: ThreadController = ThreadController()
        self.ui_controller: UIController = UIController(self.main_ui)
        self.ui_components: List[QWidget] = []
        self.project_context: Optional[ProjectContext] = None
        self.current_project_ui: Optional[ProjectUI] = None

        self.thread_controller.worker_finished.connect(self._on_auto_exclude_finished)
        self.thread_controller.worker_error.connect(self._on_auto_exclude_error)
        self.theme_manager.themeChanged.connect(self.apply_theme_to_all_windows)

        initial_theme = self.get_theme_preference()
        self.theme_manager.set_theme(initial_theme)

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> Literal[False]:
        self.cleanup()
        return False

    @log_method
    def run(self) -> None:
        self.main_ui.show_dashboard()

    @handle_exception
    @log_method
    def cleanup(self) -> None:
        logger.debug("Starting cleanup process in AppController")
        try:
            self.disconnect_signals()
            self.clean_project_context()
            self.clean_thread_controller()
            self.clean_ui_components()
            self.clean_current_project_ui()
            self.close_all_windows()
            self.check_remaining_threads()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        finally:
            logger.debug("Cleanup process in AppController completed")

    def disconnect_signals(self) -> None:
        try:
            if hasattr(self.thread_controller, "worker_finished"):
                self.thread_controller.worker_finished.disconnect(
                    self._on_auto_exclude_finished
                )
            if hasattr(self.thread_controller, "worker_error"):
                self.thread_controller.worker_error.disconnect(
                    self._on_auto_exclude_error
                )
            if hasattr(self.theme_manager, "themeChanged"):
                self.theme_manager.themeChanged.disconnect(
                    self.apply_theme_to_all_windows
                )
        except Exception as e:
            logger.debug(f"Non-critical signal disconnect warning: {e}")

    def clean_project_context(self) -> None:
        if self.project_controller and self.project_controller.project_context:
            try:
                self.project_controller.project_context.close()
            except Exception as e:
                logger.debug(f"Non-critical project context cleanup warning: {e}")

    def clean_thread_controller(self) -> None:
        if self.thread_controller:
            try:
                cleanup_event = threading.Event()
                self.thread_controller.cleanup_complete.connect(cleanup_event.set)
                self.thread_controller.cleanup_thread()
                if not cleanup_event.wait(timeout=2.0):
                    logger.warning("Thread cleanup timed out")
            except Exception as e:
                logger.debug(f"Non-critical thread cleanup warning: {e}")

    def clean_ui_components(self) -> None:
        for ui in list(self.ui_components):
            try:
                if ui:
                    ui.close()
                    ui.deleteLater()
                    self.ui_components.remove(ui)
            except Exception:
                pass

    def clean_current_project_ui(self) -> None:
        if self.current_project_ui:
            try:
                self.current_project_ui.close()
                self.current_project_ui.deleteLater()
                self.current_project_ui = None
            except Exception as e:
                logger.debug(f"Non-critical ProjectUI cleanup warning: {e}")

    def close_all_windows(self) -> None:
        try:
            QApplication.closeAllWindows()
        except Exception as e:
            logger.debug(f"Non-critical window cleanup warning: {e}")

    def check_remaining_threads(self) -> None:
        remaining_threads = threading.active_count() - 1
        if remaining_threads > 0:
            logger.debug(
                f"{remaining_threads} background threads still active during cleanup"
            )

    def get_theme_preference(self) -> str:
        theme: str = (
            self.project_controller.get_theme_preference()
            if self.project_controller
            else "light"
        )
        return theme

    def toggle_theme(self) -> str:
        new_theme: str = self.theme_manager.toggle_theme()
        self.set_theme_preference(new_theme)
        return new_theme

    def apply_theme_to_all_windows(self, theme: str) -> None:
        app = QApplication.instance()
        if app:  # Add type guard
            self.theme_manager.apply_theme_to_all_windows(app)

    def set_theme_preference(self, theme: str) -> None:
        if self.project_controller:
            self.project_controller.set_theme_preference(theme)

    @handle_exception
    @log_method
    def create_project_action(self, *args: Any) -> None:
        logger.debug("Creating project UI")
        if self.current_project_ui:
            self.current_project_ui.close()
            self.current_project_ui = None

        self.current_project_ui = self.main_ui.show_project_ui()
        if self.current_project_ui:
            self.current_project_ui.project_created.connect(self.on_project_created)
            self.ui_components.append(self.current_project_ui)
            self.current_project_ui.show()

    @handle_exception
    @log_method
    def on_project_created(self, project: Project) -> None:
        logger.info(f"Project created signal received for project: {project.name}")
        try:
            success = self.project_controller.create_project(project)
            if success:
                logger.info(f"Project {project.name} created successfully")
                self.project_context = self.project_controller.project_context
                self.project_created.emit(project)
                self.main_ui.update_project_info(project)
                self.after_project_loaded()
            else:
                logger.error(f"Failed to create project: {project.name}")
                QMessageBox.critical(
                    self.main_ui, "Error", "Failed to create project. Please try again."
                )
        except Exception as e:
            logger.exception(f"Exception occurred while creating project: {str(e)}")
            QMessageBox.critical(
                self.main_ui, "Error", f"An unexpected error occurred: {str(e)}"
            )

    @handle_exception
    @log_method
    def load_project_action(self, *args: Any) -> None:
        logger.debug("Loading project UI")
        if self.current_project_ui:
            self.current_project_ui.close()
            self.current_project_ui = None

        self.current_project_ui = self.main_ui.show_project_ui()
        if self.current_project_ui:
            self.current_project_ui.project_loaded.connect(self.on_project_loaded)
            self.ui_components.append(self.current_project_ui)
            self.current_project_ui.show()

    @handle_exception
    @log_method
    def on_project_loaded(self, project: Project) -> None:
        logger.info(f"Project loaded signal received for project: {project.name}")
        try:
            if (
                self.project_controller.current_project
                and self.project_controller.project_context
            ):
                logger.info(f"Project {project.name} loaded successfully")
                self.project_context = self.project_controller.project_context
                self.project_loaded.emit(project)
                self.main_ui.update_project_info(project)
                self.after_project_loaded()
            else:
                logger.error(
                    f"Project context not properly initialized for {project.name}"
                )
                QMessageBox.critical(
                    self.main_ui,
                    "Error",
                    "Failed to initialize project. Please try again.",
                )
        except Exception as e:
            logger.exception(
                f"Exception occurred while handling loaded project: {str(e)}"
            )
            QMessageBox.critical(
                self.main_ui, "Error", f"An unexpected error occurred: {str(e)}"
            )

    @handle_exception
    @log_method
    def after_project_loaded(self) -> None:
        try:
            logger.debug("Initializing project resources after load/create")
            self.ui_controller.reset_ui()

            if (
                not self.project_controller
                or not self.project_controller.project_context
            ):
                raise RuntimeError("Project context not initialized")

            if not self.project_controller.is_project_loaded:
                raise RuntimeError("Project not properly loaded")

            self._start_auto_exclude()

        except Exception:
            logger.error(
                "Project context not initialized. Cannot start auto-exclude thread."
            )
            QMessageBox.warning(
                self.main_ui,
                "Warning",
                "Failed to initialize project context. Some features may not work correctly.",
            )
            raise

    @handle_exception
    @log_method
    def _start_auto_exclude(self) -> None:
        try:
            if not self.project_controller.project_context:
                raise RuntimeError("Cannot start auto-exclude: No project context")

            logger.debug("Starting auto-exclude analysis")
            self.thread_controller.start_auto_exclude_thread(
                self.project_controller.project_context
            )

        except Exception as e:
            logger.error(f"Failed to start auto-exclude analysis: {str(e)}")
            raise

    @handle_exception
    @log_method
    def _on_auto_exclude_finished(self, formatted_recommendations: str) -> None:
        try:
            if not self.project_controller.project_context:
                logger.warning("No project context available for auto-exclude results")
                return

            auto_exclude_manager = (
                self.project_controller.project_context.auto_exclude_manager
            )
            if not auto_exclude_manager:
                logger.warning("No auto-exclude manager available")
                return

            if auto_exclude_manager.has_new_recommendations():
                logger.info("New auto-exclude recommendations found, showing UI")
                auto_exclude_ui = self.main_ui.show_auto_exclude_ui(
                    auto_exclude_manager,
                    self.project_controller.project_context.settings_manager,
                    formatted_recommendations,
                    self.project_controller.project_context,
                )
                self.ui_components.append(auto_exclude_ui)
            else:
                logger.info("No new exclusions to suggest")
                self.main_ui.show_dashboard()

        except Exception as e:
            logger.error(f"Error processing auto-exclude results: {str(e)}")
            self._on_auto_exclude_error(str(e))

    @handle_exception
    @log_method
    def _on_auto_exclude_error(self, error_msg: str) -> None:
        logger.error(f"Auto-exclude error: {error_msg}")
        QMessageBox.critical(
            self.main_ui,
            "Error",
            f"An error occurred during auto-exclusion:\n{error_msg}",
        )
        self.main_ui.show_dashboard()

    @handle_exception
    @log_method
    def manage_projects(self, *args: Any) -> None:
        logger.debug("Opening project management UI")
        project_management_ui = self.main_ui.show_project_management()
        project_management_ui.project_deleted.connect(self._handle_project_deleted)
        self.ui_components.append(project_management_ui)

    @handle_exception
    @log_method
    def _handle_project_deleted(self, project_name: str) -> None:
        logger.info(f"Project deleted: {project_name}")
        if (
            self.project_controller.current_project
            and self.project_controller.current_project.name.lower()
            == project_name.lower()
        ):
            self.cleanup_current_project()
            self.main_ui.status_bar.showMessage("Ready")

    @handle_exception
    @log_method
    def cleanup_current_project(self) -> None:
        if self.project_controller:
            if self.project_controller.project_context:
                self.project_controller.project_context.close()
            self.project_controller.current_project = None
            self.project_controller.project_context = None
            self.project_context = None
            self.ui_controller.reset_ui()

    @handle_exception
    @log_method
    def manage_exclusions(self, *args: Any) -> None:
        if self.project_controller and self.project_controller.project_context:
            exclusions_manager_ui = self.ui_controller.manage_exclusions(
                self.project_controller.project_context.settings_manager
            )
            self.ui_components.append(exclusions_manager_ui)
        else:
            logger.error("No project context available.")
            QMessageBox.warning(
                self.main_ui,
                "Error",
                "No project is currently loaded. Please load a project first.",
            )

    @handle_exception
    @log_method
    def view_directory_tree(self, *args: Any) -> None:
        if self.project_controller and self.project_controller.project_context:
            result = self.project_controller.project_context.get_directory_tree()
            directory_tree_ui = self.ui_controller.view_directory_tree(result)
            self.ui_components.append(directory_tree_ui)
        else:
            logger.error("Cannot view directory tree: project_context is None.")
            QMessageBox.warning(
                self.main_ui,
                "Error",
                "No project is currently loaded. Please load a project first.",
            )

    @handle_exception
    @log_method
    def analyze_directory(self, *args: Any) -> None:
        if self.project_controller and self.project_controller.project_context:
            result_ui = self.ui_controller.show_result(
                self.project_controller.project_context.directory_analyzer
            )
            if result_ui is not None:
                result_ui.update_result()
            else:
                logger.error("ResultUI could not be initialized.")
        else:
            logger.error("Cannot analyze directory: project_context is None.")
            QMessageBox.warning(
                self.main_ui,
                "Error",
                "No project is currently loaded. Please load a project first.",
            )
