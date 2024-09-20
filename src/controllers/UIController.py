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

    def show_auto_exclude_ui(self, auto_exclude_manager, settings_manager, formatted_recommendations, project_context):
        """Show auto-exclude UI with given recommendations."""
        return self.main_ui.show_auto_exclude_ui(auto_exclude_manager, settings_manager, formatted_recommendations, project_context)

    def manage_exclusions(self, settings_manager):
        """Show exclusions management UI."""
        return self.main_ui.manage_exclusions(settings_manager)

    def update_project_info(self, project):
        """Update the project information displayed in the UI."""
        self.main_ui.update_project_info(project)

    def view_directory_tree(self, result):
        """Show directory tree UI given result."""
        return self.main_ui.view_directory_tree(result)

    def show_result(self, directory_analyzer):
        """Show result UI given directory analyzer."""
        return self.main_ui.show_result(directory_analyzer)

    def show_error_message(self, title, message):
        """Display an error message to the user."""
        self.main_ui.show_error_message(title, message)

    def show_dashboard(self):
        """Show the main dashboard."""
        self.main_ui.show_dashboard()