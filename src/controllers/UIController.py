"""
GynTree: UIController manages the interaction between the project and the UI.
This controller is responsible for updating and resetting UI components whenever
a new project is loaded or created. It ensures that the correct project information
is displayed and that the user interface reflects the current project state.

Responsibilities:
- Reset and update UI components like the directory tree, exclusions, and analysis.
- Manage exclusion-related UI elements.
- Provide a clean interface for displaying project information in the main UI.
"""

import logging

from PyQt5.QtCore import QMetaObject, QObject, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMessageBox

from components.UI.ResultUI import ResultUI

logger = logging.getLogger(__name__)


class UIController:
    def __init__(self, main_ui):
        self.main_ui = main_ui

    def reset_ui(self):
        """Reset UI components like directory tree, exclusions, and analysis."""
        logger.debug("Resetting UI components for new project...")
        self.main_ui.clear_directory_tree()
        self.main_ui.clear_analysis()
        self.main_ui.clear_exclusions()

    def show_auto_exclude_ui(
        self,
        auto_exclude_manager,
        settings_manager,
        formatted_recommendations,
        project_context,
    ):
        """Show auto-exclude UI with given recommendations."""
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

    def manage_exclusions(self, settings_manager):
        """Show exclusions management UI."""
        try:
            return self.main_ui.manage_exclusions(settings_manager)
        except Exception as e:
            logger.error(f"Error managing exclusions: {str(e)}")
            self.show_error_message(
                "Exclusion Management Error", f"Failed to manage exclusions: {str(e)}"
            )

    def update_project_info(self, project):
        """Update project information displayed in the UI."""
        try:
            self.main_ui.update_project_info(project)
        except Exception as e:
            logger.error(f"Error updating project info: {str(e)}")
            self.show_error_message(
                "Update Error", f"Failed to update project information: {str(e)}"
            )

    def view_directory_tree(self, result):
        """Show directory tree UI given the result."""
        try:
            return self.main_ui.view_directory_tree_ui(result)
        except Exception as e:
            logger.error(f"Error viewing directory tree: {str(e)}")
            self.show_error_message(
                "View Error", f"Failed to view directory tree: {str(e)}"
            )

    def show_result(self, directory_analyzer):
        """Show result UI given directory analyzer."""
        try:
            return self.main_ui.show_result(directory_analyzer)
        except Exception as e:
            logger.error(f"Error showing results: {str(e)}")
            self.show_error_message("Result Error", f"Failed to show results: {str(e)}")

    def update_ui(self, component, data):
        """Update UI component with given data."""
        try:
            QMetaObject.invokeMethod(
                component, "update_data", Qt.QueuedConnection, data
            )
        except Exception as e:
            logger.error(f"Error updating UI component: {str(e)}")
            self.show_error_message(
                "Update Error", f"Failed to update UI component: {str(e)}"
            )

    def show_error_message(self, title, message):
        """Display an error message to the user."""
        try:
            self.main_ui.show_error_message(title, message)
        except Exception as e:
            logger.error(f"Failed to show error message: {str(e)}")
            # Fallback to QMessageBox if main_ui error display fails
            QMessageBox.critical(None, title, message)

    def show_dashboard(self):
        """Show the main dashboard."""
        try:
            self.main_ui.show_dashboard()
        except Exception as e:
            logger.error(f"Error showing dashboard: {str(e)}")
            self.show_error_message(
                "Dashboard Error", f"Failed to show dashboard: {str(e)}"
            )
