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
        exclusions = self.default_exclusions.copy()
        for project_type, is_detected in project_info.items():
            if is_detected:
                exclusions.update(self._get_project_type_exclusions(project_type, start_directory))
        
        if self._has_init_files(start_directory):
            exclusions.add('**/__init__.py')
        
        logger.debug(f"Root exclusions for project: {exclusions}")
        return exclusions

    def _get_project_type_exclusions(self, project_type: str, start_directory: str) -> Set[str]:
        exclusions = set()
        for exclusion in self.project_type_exclusions.get(project_type, set()):
            exclusion_path = os.path.join(start_directory, exclusion)
            if os.path.exists(exclusion_path):
                exclusions.add(exclusion)
        return exclusions

    def _has_init_files(self, directory: str) -> bool:
        for root, _, files in os.walk(directory):
            if '__init__.py' in files:
                return True
        return False

    def merge_with_existing_exclusions(self, existing_exclusions: Set[str], new_exclusions: Set[str]) -> Set[str]:
        merged_exclusions = existing_exclusions.union(new_exclusions)
        logger.info(f"Merged root exclusions: {merged_exclusions}")
        return merged_exclusions

    def add_project_type_exclusion(self, project_type: str, exclusions: Set[str]):
        if project_type in self.project_type_exclusions:
            self.project_type_exclusions[project_type].update(exclusions)
        else:
            self.project_type_exclusions[project_type] = exclusions
        logger.info(f"Added exclusions for project type {project_type}: {exclusions}")

    def remove_project_type_exclusion(self, project_type: str, exclusions: Set[str]):
        if project_type in self.project_type_exclusions:
            self.project_type_exclusions[project_type] -= exclusions
            logger.info(f"Removed exclusions for project type {project_type}: {exclusions}")