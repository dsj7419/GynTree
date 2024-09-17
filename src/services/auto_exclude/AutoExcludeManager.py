import os
from services.auto_exclude.PythonAutoExclude import PythonAutoExclude
from services.auto_exclude.IDEandGitAutoExclude import IDEandGitAutoExclude

class AutoExcludeManager:
    def __init__(self, start_directory, project_type='python'):
        self.start_directory = start_directory
        self.project_type = project_type
        self.exclusion_services = []
        if self.project_type == 'python':
            self.exclusion_services.append(PythonAutoExclude(self.start_directory))
            self.exclusion_services.append(IDEandGitAutoExclude(self.start_directory))

    def get_grouped_recommendations(self, current_settings):
        recommendations = {'directories': set(), 'files': set()}
        excluded_dirs = set(current_settings.get('excluded_dirs', []))
        excluded_files = set(current_settings.get('excluded_files', []))
        for service in self.exclusion_services:
            service_exclusions = service.get_exclusions()
            for dir_path in service_exclusions['directories']:
                if not any(os.path.normpath(dir_path).startswith(os.path.normpath(excluded_dir)) for excluded_dir in excluded_dirs):
                    recommendations['directories'].add(dir_path)
            for file_path in service_exclusions['files']:
                if file_path not in excluded_files:
                    recommendations['files'].add(file_path)
        return recommendations

    def check_for_new_exclusions(self, current_settings):
        """
        Compares the current settings to the recommended exclusions to see if any new exclusions are found.
        Returns True if new exclusions are found, False otherwise.
        """
        recommendations = self.get_grouped_recommendations(current_settings)
        excluded_dirs = set(current_settings.get('excluded_dirs', []))
        excluded_files = set(current_settings.get('excluded_files', []))

        for dir in recommendations['directories']:
            if dir not in excluded_dirs:
                return True
        for file in recommendations['files']:
            if file not in excluded_files:
                return True
        return False
