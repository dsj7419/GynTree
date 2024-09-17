"""
GynTree: This file defines the IDEandGitAutoExclude class, which identifies IDE and Git-related files and directories for exclusion.
"""
import os

class IDEandGitAutoExclude:
    def __init__(self, start_directory):
        self.start_directory = start_directory

    def get_exclusions(self):
        """
        Identify and return IDE and Git-related directories to exclude.
        This includes:
        - .git
        - venv (virtual environments)
        - .vs (Visual Studio folders)
        """
        recommendations = {'directories': set(), 'files': set()}

        for root, dirs, _ in os.walk(self.start_directory):
            for directory in dirs:
                if directory in [".git", ".vs", "venv"]:
                    # Add these directories to the directory exclusion list
                    recommendations['directories'].add(os.path.join(root, directory))

        return recommendations
