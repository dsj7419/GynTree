"""
GynTree: This file defines the IDEandGitAutoExclude class, which identifies IDE and Git-related files and directories for exclusion.
"""
import os
from services.ExclusionService import ExclusionService

class IDEandGitAutoExclude(ExclusionService):
    def __init__(self, start_directory):
        super().__init__(start_directory)

    def get_exclusions(self):
        recommendations = {'directories': set(), 'files': set()}

        for root, dirs, files in os.walk(self.start_directory):
            for directory in dirs:
                if directory in [".git", ".vs", "venv", "__pycache__", "build", "dist"]:
                    recommendations['directories'].add(os.path.join(root, directory))

            for file in files:
                if file in ['.gitignore', '.vsignore', 'requirements.txt', '.dockerignore', 'Thumbs.db', '.DS_Store']:
                    recommendations['files'].add(os.path.join(root, file))
                
                # Exclude executables
                if file.endswith(('.exe', '.dll', '.so', '.dylib')):
                    recommendations['files'].add(os.path.join(root, file))

        return recommendations