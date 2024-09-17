"""
GynTree: This file contains the AppController class, which serves as the main controller for the application.
It manages the flow between different components and handles user interactions.
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

    def run(self):
        self.main_ui.show_dashboard()

    def create_project(self):
        self.project_ui = self.main_ui.show_project_ui()
        self.project_ui.create_project_btn.clicked.connect(self.create_project_action)

    def create_project_action(self):
        project = self.project_ui.create_project()
        if project:
            self.current_project = project
            self.main_ui.update_project_info(self.current_project)
            self.directory_analyzer = DirectoryAnalyzer(self.current_project.start_directory, SettingsManager(self.current_project))
            self.trigger_auto_exclude()
        self.project_ui.close()

    def load_project(self):
        self.project_ui = self.main_ui.show_project_ui()
        self.project_ui.load_project_btn.clicked.connect(self.load_project_action)

    def load_project_action(self):
        project = self.project_ui.load_project()
        if project:
            self.current_project = project
            self.main_ui.update_project_info(self.current_project)
            self.directory_analyzer = DirectoryAnalyzer(self.current_project.start_directory, SettingsManager(self.current_project))
            self.trigger_auto_exclude()
            self.project_ui.close()
        else:
            print("No project selected or something went wrong.")

    def trigger_auto_exclude(self):
        if self.current_project:
            auto_exclude_manager = AutoExcludeManager(self.current_project.start_directory)
            settings_manager = SettingsManager(self.current_project)
            if auto_exclude_manager.check_for_new_exclusions(settings_manager.settings):
                self.main_ui.show_auto_exclude_ui(auto_exclude_manager, settings_manager)
            else:
                print("No new exclusions to suggest.")

    def manage_exclusions(self):
        if self.current_project:
            settings_manager = SettingsManager(self.current_project)
            self.main_ui.manage_exclusions(settings_manager)

    def analyze_directory(self):
        if self.current_project and self.directory_analyzer:
            result = self.directory_analyzer.analyze_directory()
            self.main_ui.show_result(result)

    def view_directory_tree(self):
        if self.current_project and self.directory_analyzer:
            self.main_ui.view_directory_tree(self.directory_analyzer)

if __name__ == "__main__":
    app = QApplication([])
    controller = AppController()
    controller.run()
    app.exec_()