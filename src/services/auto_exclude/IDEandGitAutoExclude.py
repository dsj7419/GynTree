import os
from typing import Dict, Set
from services.ExclusionService import ExclusionService
from services.ProjectTypeDetector import ProjectTypeDetector
from services.SettingsManager import SettingsManager
import logging

logger = logging.getLogger(__name__)

class IDEandGitAutoExclude(ExclusionService):
    def __init__(self, start_directory: str, project_type_detector: ProjectTypeDetector, settings_manager: SettingsManager):
        super().__init__(start_directory, project_type_detector, settings_manager)

    def get_exclusions(self) -> Dict[str, Set[str]]:
        recommendations = {'root_exclusions': set(), 'excluded_dirs': set(), 'excluded_files': set()}

        common_root_exclusions = {'.git', '.vs', '.idea', '.vscode'}
        recommendations['root_exclusions'].update(common_root_exclusions)
        logger.debug(f"IDEandGitAutoExclude: Adding common root exclusions: {common_root_exclusions}")

        common_file_exclusions = {
            '.gitignore', '.vsignore', '.dockerignore', '.gitattributes',
            'Thumbs.db', '.DS_Store', '*.swp', '*~',
            '.editorconfig'
        }
        recommendations['excluded_files'].update(common_file_exclusions)
        logger.debug(f"IDEandGitAutoExclude: Recommending common file exclusions: {common_file_exclusions}")

        for root, dirs, files in self.walk_directory():
            for file in files:
                if file.endswith(('.log', '.tmp', '.bak', '.orig', '.user')):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, self.start_directory)
                    recommendations['excluded_files'].add(relative_path)
                    logger.debug(f"IDEandGitAutoExclude: Recommending exclusion of file {relative_path}")

        return recommendations