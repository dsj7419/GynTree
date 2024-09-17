# GynTree: Defines exclusion rules specific to Python projects and environments.

import os
from services.ExclusionService import ExclusionService

class PythonAutoExclude(ExclusionService):
    def __init__(self, start_directory):
        super().__init__(start_directory)

    def get_exclusions(self):
        recommendations = {'directories': set(), 'files': set()}

        for root, dirs, files in os.walk(self.start_directory):
            for dir in ['__pycache__', '.pytest_cache', 'build', 'dist', '.tox']:
                if dir in dirs:
                    recommendations['directories'].add(os.path.join(root, dir))

            for file in files:
                if file.endswith(('.pyc', '.pyo', '.coverage')):
                    recommendations['files'].add(os.path.join(root, file))
                elif file == '__init__.py':
                    recommendations['files'].add(os.path.join(root, file))

            for venv in ['venv', '.venv', 'env']:
                if venv in dirs:
                    recommendations['directories'].add(os.path.join(root, venv))

        if os.path.exists(os.path.join(self.start_directory, 'setup.py')) or \
           os.path.exists(os.path.join(self.start_directory, 'requirements.txt')) or \
           os.path.exists(os.path.join(self.start_directory, 'pyproject.toml')):
            recommendations['directories'].add(os.path.join(self.start_directory, 'build'))
            recommendations['directories'].add(os.path.join(self.start_directory, 'dist'))

        return recommendations