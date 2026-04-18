import logging
from typing import Any, Dict, Optional

from PyQt5.QtCore import QMetaObject, Qt
from PyQt5.QtWidgets import QMessageBox, QWidget

from components.UI.AutoExcludeUI import AutoExcludeUI
from components.UI.DirectoryTreeUI import DirectoryTreeUI
from components.UI.ExclusionsManagerUI import ExclusionsManagerUI
from components.UI.ResultUI import ResultUI
from models.Project import Project
from services.auto_exclude.AutoExcludeManager import AutoExcludeManager
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.SettingsManager import SettingsManager

logger = logging.getLogger(__name__)


class UIController:
    def __init__(self, main_ui: Any) -> None:
        self.main_ui = main_ui

    def reset_ui(self) -> None:
        logger.debug("Resetting UI components for new project...")
        self.main_ui.clear_directory_tree()
        self.main_ui.clear_analysis()
        self.main_ui.clear_exclusions()

    def show_auto_exclude_ui(
        self,
        auto_exclude_manager: AutoExcludeManager,
        settings_manager: SettingsManager,
        formatted_recommendations: Dict[str, Any],
        project_context: Any,
    ) -> Optional[AutoExcludeUI]:
        try:
            return self.main_ui.show_auto_exclude_ui(
                auto_exclude_manager,
                settings_manager,
                formatted_recommendations,
                project_context,
            )
        except Exception as e:
            logger.error(f"Error showing auto-exclude UI: {str(e)}")
            self.show_error_message(
                "Auto-Exclude Error", f"Failed to show auto-exclude UI: {str(e)}"
            )
            return None

    def manage_exclusions(
        self, settings_manager: SettingsManager
    ) -> Optional[ExclusionsManagerUI]:
        try:
            return self.main_ui.manage_exclusions(settings_manager)
        except Exception as e:
            logger.error(f"Error managing exclusions: {str(e)}")
            self.show_error_message(
                "Exclusion Management Error", f"Failed to manage exclusions: {str(e)}"
            )
            return None

    def update_project_info(self, project: Project) -> None:
        try:
            self.main_ui.update_project_info(project)
        except Exception as e:
            logger.error(f"Error updating project info: {str(e)}")
            self.show_error_message(
                "Update Error", f"Failed to update project information: {str(e)}"
            )

    def view_directory_tree(self, result: Dict[str, Any]) -> Optional[DirectoryTreeUI]:
        try:
            return self.main_ui.view_directory_tree_ui(result)
        except Exception as e:
            logger.error(f"Error viewing directory tree: {str(e)}")
            self.show_error_message(
                "View Error", f"Failed to view directory tree: {str(e)}"
            )
            return None

    def show_result(self, directory_analyzer: DirectoryAnalyzer) -> Optional[ResultUI]:
        try:
            return self.main_ui.show_result(directory_analyzer)
        except Exception as e:
            logger.error(f"Error showing results: {str(e)}")
            self.show_error_message("Result Error", f"Failed to show results: {str(e)}")
            return None

    def update_ui(self, component: QWidget, data: Any) -> None:
        try:
            QMetaObject.invokeMethod(
                component, "update_data", Qt.QueuedConnection, data
            )
        except Exception as e:
            logger.error(f"Error updating UI component: {str(e)}")
            self.show_error_message(
                "Update Error", f"Failed to update UI component: {str(e)}"
            )

    def show_error_message(self, title: str, message: str) -> None:
        try:
            self.main_ui.show_error_message(title, message)
        except Exception as e:
            logger.error(f"Failed to show error message: {str(e)}")
            QMessageBox.critical(None, title, message)

    def show_dashboard(self) -> None:
        try:
            self.main_ui.show_dashboard()
        except Exception as e:
            logger.error(f"Error showing dashboard: {str(e)}")
            self.show_error_message(
                "Dashboard Error", f"Failed to show dashboard: {str(e)}"
            )
