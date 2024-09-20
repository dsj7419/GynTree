import os
import logging
from typing import List, Dict, Set
from services.ExclusionService import ExclusionService
from services.ExclusionServiceFactory import ExclusionServiceFactory
from services.ProjectTypeDetector import ProjectTypeDetector
from services.SettingsManager import SettingsManager

logger = logging.getLogger(__name__)

class AutoExcludeManager:
    def __init__(self, start_directory: str, settings_manager: SettingsManager, project_types: Set[str], project_type_detector: ProjectTypeDetector):
        self.start_directory = os.path.abspath(start_directory)
        self.settings_manager = settings_manager
        self.project_types = project_types
        self.exclusion_services: List[ExclusionService] = ExclusionServiceFactory.create_services(
            project_types,
            self.start_directory,
            project_type_detector,
            settings_manager
        )
        logger.debug(f"Created exclusion services: {[type(service).__name__ for service in self.exclusion_services]}")
        self.raw_recommendations: Dict[str, Set[str]] = {'root_exclusions': set(), 'excluded_dirs': set(), 'excluded_files': set()}

    def get_recommendations(self) -> Dict[str, Set[str]]:
        self.raw_recommendations = {'root_exclusions': set(), 'excluded_dirs': set(), 'excluded_files': set()}
        
        for service in self.exclusion_services:
            service_exclusions = service.get_exclusions()
            for category in ['root_exclusions', 'excluded_dirs', 'excluded_files']:
                self.raw_recommendations[category].update(service_exclusions.get(category, set()))

        # Filter out already excluded items
        for category in ['root_exclusions', 'excluded_dirs', 'excluded_files']:
            self.raw_recommendations[category] = {
                path for path in self.raw_recommendations[category]
                if not self.settings_manager.is_excluded(os.path.join(self.start_directory, path))
            }

        return self.raw_recommendations

    def get_formatted_recommendations(self) -> str:
        recommendations = self.get_recommendations()
        lines = []
        for category in ['root_exclusions', 'excluded_dirs', 'excluded_files']:
            if recommendations[category]:
                lines.append(f"{category.replace('_', ' ').title()}:")
                for path in sorted(recommendations[category]):
                    lines.append(f" - {path}")
                lines.append("")
        return "\n".join(lines)

    def apply_recommendations(self):
        recommendations = self.get_recommendations()
        current_settings = self.settings_manager.settings
        current_settings['root_exclusions'] = list(set(current_settings.get('root_exclusions', [])) | recommendations['root_exclusions'])
        current_settings['excluded_dirs'] = list(set(current_settings.get('excluded_dirs', [])) | recommendations['excluded_dirs'])
        current_settings['excluded_files'] = list(set(current_settings.get('excluded_files', [])) | recommendations['excluded_files'])
        self.settings_manager.update_settings(current_settings)