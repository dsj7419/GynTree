"""
GynTree: This file defines the WebAutoExclude class, which identifies web-related files and directories for exclusion.
"""
import os
from services.ExclusionService import ExclusionService

class WebAutoExclude(ExclusionService):
    def __init__(self, start_directory):
        super().__init__(start_directory)

    def get_exclusions(self):
        recommendations = {'directories': set(), 'files': set()}

        for root, dirs, files in os.walk(self.start_directory):
            for dir in ['dist', 'build', 'out']:
                if dir in dirs:
                    recommendations['directories'].add(os.path.join(root, dir))

            for dir in ['.cache', '.tmp']:
                if dir in dirs:
                    recommendations['directories'].add(os.path.join(root, dir))

            for file in files:
                if file in ['.eslintrc.json', '.prettierrc', 'tsconfig.json', 'tailwind.config.js']:
                    recommendations['files'].add(os.path.join(root, file))

        return recommendations