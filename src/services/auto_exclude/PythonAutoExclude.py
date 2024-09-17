import os

class PythonAutoExclude:
    def __init__(self, start_directory):
        self.start_directory = start_directory

    def get_exclusions(self):
        """
        Gather both directory and file exclusions.
        """
        recommendations = {'directories': set(), 'files': set()}

        # Exclude directories like __pycache__ and .pytest_cache
        recommendations['directories'].update(self._get_exclusions_by_name("__pycache__"))
        recommendations['directories'].update(self._get_exclusions_by_name(".pytest_cache"))

        # Exclude .pyc and __init__.py files
        recommendations['files'].update(self.get_pyc_file_exclusions())
        recommendations['files'].update(self.get_init_file_exclusions())

        return recommendations

    def get_pyc_file_exclusions(self):
        """
        Gather .pyc files for exclusion.
        """
        recommendations = set()
        for root, _, files in os.walk(self.start_directory):
            for file in files:
                if file.endswith('.pyc'):
                    recommendations.add(os.path.join(root, file))
        return recommendations

    def get_init_file_exclusions(self):
        """
        Gather __init__.py files for exclusion.
        """
        recommendations = set()
        for root, _, files in os.walk(self.start_directory):
            for file in files:
                if file == '__init__.py':
                    recommendations.add(os.path.join(root, file))
        return recommendations

    def _get_exclusions_by_name(self, folder_name):
        """
        Exclude directories by name (e.g., __pycache__, .pytest_cache).
        """
        recommendations = set()
        for root, dirs, _ in os.walk(self.start_directory):
            for directory in dirs:
                if directory == folder_name:
                    recommendations.add(os.path.join(root, directory))
        return recommendations
