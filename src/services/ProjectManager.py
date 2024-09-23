"""
GynTree: This file contains the ProjectManager class, which handles project-related operations.
It manages creating, loading, and saving projects, as well as maintaining project metadata.
"""

import json
import os
from models.Project import Project

class ProjectManager:
    projects_dir = 'config/projects'

    def __init__(self):
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)

    def save_project(self, project):
        """Save a project to a JSON file."""
        project_file = os.path.join(self.projects_dir, f'{project.name}.json')
        with open(project_file, 'w') as f:
            json.dump(project.to_dict(), f, indent=4)

    def load_project(self, project_name):
        """Load a project from a JSON file."""
        project_file = os.path.join(self.projects_dir, f'{project_name}.json')
        if os.path.exists(project_file):
            with open(project_file, 'r') as f:
                data = json.load(f)
            return Project.from_dict(data)
        return None

    def list_projects(self):
        """List all saved projects."""
        projects = []
        for filename in os.listdir(self.projects_dir):
            if filename.endswith('.json'):
                project_name = filename[:-5]
                projects.append(project_name)
        return projects
    
    def delete_project(self, project_name):
        project_file = os.path.join(self.projects_dir, f"{project_name}.json")
        if os.path.exists(project_file):
            os.remove(project_file)
            return True
        return False

    def cleanup(self):
        """Perform any necessary cleanup operations."""
        pass