import logging
import os
from typing import Set, Dict

logger = logging.getLogger(__name__)

class RootExclusionManager:
    def __init__(self):
        self.default_exclusions = {'.git'}
        self.project_type_exclusions = {
            'web': {'node_modules', '.next', 'dist', 'build', 'out'},
            'nextjs': {'node_modules', '.next', 'dist', 'build', 'out'},
            'javascript': {'node_modules', 'dist', 'build'},
            'python': {'venv', '__pycache__', '.pytest_cache'},
            'database': {'prisma', 'migrations'}
        }

    def get_root_exclusions(self, project_info: Dict[str, bool], start_directory: str) -> Set[str]:
        """
        Get root exclusions for a project based on project type and directory.
        
        Args:
            project_info: Dictionary mapping project types to boolean detection status
            start_directory: Base directory path for the project
            
        Returns:
            Set of exclusion patterns for the project
        """
        exclusions = self.default_exclusions.copy()
        for project_type, is_detected in project_info.items():
            if is_detected:
                exclusions.update(self._get_project_type_exclusions(project_type, start_directory))
        
        if self._has_init_files(start_directory):
            exclusions.add('**/__init__.py')
        
        logger.debug(f"Root exclusions for project: {exclusions}")
        return exclusions

    def _get_project_type_exclusions(self, project_type: str, start_directory: str) -> Set[str]:
        """
        Get exclusions for a specific project type.
        
        Args:
            project_type: Type of project (e.g., 'python', 'javascript')
            start_directory: Base directory path
            
        Returns:
            Set of exclusion patterns for the project type
        """
        return self.project_type_exclusions.get(project_type, set())

    def _has_init_files(self, directory: str) -> bool:
        """
        Check if directory contains any __init__.py files.
        
        Args:
            directory: Directory path to check
            
        Returns:
            True if __init__.py files are found, False otherwise
        """
        for root, _, files in os.walk(directory):
            if '__init__.py' in files:
                return True
        return False

    def merge_with_existing_exclusions(self, existing_exclusions: Set[str], new_exclusions: Set[str]) -> Set[str]:
        """
        Merge two sets of exclusions.
        
        Args:
            existing_exclusions: Current set of exclusions
            new_exclusions: New exclusions to add
            
        Returns:
            Merged set of exclusions
        """
        merged_exclusions = existing_exclusions.union(new_exclusions)
        logger.info(f"Merged root exclusions: {merged_exclusions}")
        return merged_exclusions

    def add_project_type_exclusion(self, project_type: str, exclusions: Set[str]):
            """
            Add exclusions for a project type.
            
            Args:
                project_type: Type of project to add exclusions for
                exclusions: Set of exclusion patterns to add
                
            Note:
                If project type already exists, exclusions will be added to existing set.
                If project type doesn't exist, a new set will be created.
            """
            if project_type in self.project_type_exclusions:
                self.project_type_exclusions[project_type].update(exclusions)
            else:
                self.project_type_exclusions[project_type] = exclusions
            logger.info(f"Added exclusions for project type {project_type}: {exclusions}")

    def remove_project_type_exclusion(self, project_type: str, exclusions: Set[str]):
        """
        Remove specific exclusions from a project type.
        
        Args:
            project_type: Type of project to remove exclusions from
            exclusions: Set of exclusion patterns to remove
            
        Note:
            If project type exists, specified exclusions will be removed.
            If project type doesn't exist, no action will be taken.
        """
        if project_type in self.project_type_exclusions:
            self.project_type_exclusions[project_type] -= exclusions
            logger.info(f"Removed exclusions for project type {project_type}: {exclusions}")
