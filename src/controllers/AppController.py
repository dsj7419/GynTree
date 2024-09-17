"""
GynTree: This module contains the AppController class, which serves as the main controller.
It manages the flow between different components, handles user interactions,
and coordinates various operations like project creation, analysis, and result display.
The AppController acts as the central hub for application logic and user interface updates.
"""

from PyQt5.QtWidgets import QApplication
from components.UI.DashboardUI import DashboardUI
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.ProjectManager import ProjectManager
from services.SettingsManager import SettingsManager
from services.auto_exclude.AutoExcludeManager import AutoExcludeManager

class AppController:
    def __init__(self):
        self.project_manager = ProjectManager()
        self.current_project = None
        self.main_ui = DashboardUI(self)
        self.project_ui = None
        self.directory_analyzer = None
        self.settings_manager = None

    def run(self):
        self.main_ui.show_dashboard()

    def create_project(self):
        self.project_ui = self.main_ui.show_project_ui()
        self.project_ui.create_project_btn.clicked.connect(self.create_project_action)

    def create_project_action(self):
        project = self.project_ui.create_project()
        if project:
            self.current_project = project
            self.settings_manager = SettingsManager(self.current_project)
            self.main_ui.update_project_info(self.current_project)
            self.trigger_auto_exclude()
            self.initialize_directory_analyzer()
        self.project_ui.close()

    def load_project(self):
        self.project_ui = self.main_ui.show_project_ui()
        self.project_ui.load_project_btn.clicked.connect(self.load_project_action)

    def load_project_action(self):
        project = self.project_ui.load_project()
        if project:
            self.current_project = project
            self.settings_manager = SettingsManager(self.current_project)
            self.main_ui.update_project_info(self.current_project)
            self.initialize_directory_analyzer()
            self.project_ui.close()
        else:
            print("No project selected or something went wrong.")

    def trigger_auto_exclude(self):
        if self.current_project:
            auto_exclude_manager = AutoExcludeManager(self.current_project.start_directory)
            if auto_exclude_manager.check_for_new_exclusions(self.settings_manager.settings):
                formatted_recommendations = auto_exclude_manager.get_formatted_recommendations()
                self.main_ui.show_auto_exclude_ui(auto_exclude_manager, self.settings_manager, formatted_recommendations)
            else:
                print("No new exclusions to suggest.")

    def initialize_directory_analyzer(self):
        self.directory_analyzer = DirectoryAnalyzer(self.current_project.start_directory, self.settings_manager)

    def manage_exclusions(self):
        if self.current_project:
            self.main_ui.manage_exclusions(self.settings_manager)

    def analyze_directory(self):
        if self.current_project and self.directory_analyzer:
            result = self.directory_analyzer.get_flat_structure()
            self.main_ui.show_result(result)

    def view_directory_tree(self):
        if self.current_project and self.directory_analyzer:
            result = self.directory_analyzer.analyze_directory()
            self.main_ui.view_directory_tree(result)

if __name__ == "__main__":
    app = QApplication([])
    controller = AppController()
    controller.run()
    app.exec_()