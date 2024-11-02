"""
GynTree: This file contains the ProjectManager class, which handles project-related operations.
It manages creating, loading, and saving projects, as well as maintaining project metadata.
"""
import json
import os
import logging
from typing import Optional, List
from models.Project import Project

logger = logging.getLogger(__name__)

class ProjectManager:
    projects_dir = 'config/projects'
    
    def __init__(self):
        """
        Initialize project manager and ensure projects directory exists.
        
        Raises:
            PermissionError: If directory cannot be created due to permissions
            OSError: If directory cannot be created due to other OS errors
        """
        # Always try to create directory
        os.makedirs(self.projects_dir, exist_ok=True)
            
    def save_project(self, project: Project) -> None:
        """
        Save a project to a JSON file.
        
        Args:
            project: Project instance to save
            
        Raises:
            OSError: If file cannot be written
        """
        project_file = os.path.join(self.projects_dir, f'{project.name}.json')
        try:
            with open(project_file, 'w') as f:
                json.dump(project.to_dict(), f, indent=4)
        except (PermissionError, OSError) as e:
            logger.error(f"Failed to save project {project.name}: {e}")
            raise

    def load_project(self, project_name: str) -> Optional[Project]:
        """
        Load a project from a JSON file.
        
        Args:
            project_name: Name of project to load
            
        Returns:
            Project instance if successful, None if project doesn't exist or can't be loaded
        """
        project_file = os.path.join(self.projects_dir, f'{project_name}.json')
        if not os.path.exists(project_file):
            return None
            
        try:
            with open(project_file, 'r') as f:
                data = json.load(f)
            return Project.from_dict(data)
        except (PermissionError, OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load project {project_name}: {e}")
            return None

    def list_projects(self) -> List[str]:
        """
        List all saved projects.
        
        Returns:
            List of project names
        """
        try:
            projects = []
            for filename in os.listdir(self.projects_dir):
                if filename.endswith('.json'):
                    project_name = filename[:-5]
                    projects.append(project_name)
            return projects
        except (PermissionError, OSError) as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    def delete_project(self, project_name: str) -> bool:
        """
        Delete a project configuration file.
        
        Args:
            project_name: Name of project to delete
            
        Returns:
            True if project was deleted, False otherwise
        """
        project_file = os.path.join(self.projects_dir, f"{project_name}.json")
        try:
            if os.path.exists(project_file):
                os.remove(project_file)
                return True
            return False
        except (PermissionError, OSError) as e:
            logger.error(f"Failed to delete project {project_name}: {e}")
            return False

    def cleanup(self) -> None:
        """Perform any necessary cleanup operations."""
        pass