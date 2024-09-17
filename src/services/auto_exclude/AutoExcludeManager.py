# GynTree: Manages the automatic exclusion rules for files and directories during analysis.

import os
import logging
from typing import List, Dict
from services.ExclusionService import ExclusionService
from services.ProjectTypeDetector import ProjectTypeDetector
from services.ExclusionServiceFactory import ExclusionServiceFactory
from services.ExclusionAggregator import ExclusionAggregator

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AutoExcludeManager:
    def __init__(self, start_directory: str):
        self.start_directory = start_directory
        self.project_types = ProjectTypeDetector(start_directory).detect_project_types()
        logger.debug(f"Detected project types: {self.project_types}")
        self.exclusion_services: List[ExclusionService] = ExclusionServiceFactory.create_services(self.project_types, start_directory)
        logger.debug(f"Created exclusion services: {[type(service).__name__ for service in self.exclusion_services]}")
        self.raw_recommendations = None
        self.formatted_recommendations = None

    def get_grouped_recommendations(self, current_settings: Dict[str, List[str]]) -> Dict[str, set]:
        if self.raw_recommendations is None:
            self.raw_recommendations = {'directories': set(), 'files': set()}
            excluded_dirs = set(current_settings.get('excluded_dirs', []))
            excluded_files = set(current_settings.get('excluded_files', []))
            
            for service in self.exclusion_services:
                service_exclusions = service.get_exclusions()
                logger.debug(f"Exclusions from {type(service).__name__}: {service_exclusions}")
                for dir_path in service_exclusions['directories']:
                    if not any(os.path.normpath(dir_path).startswith(os.path.normpath(excluded_dir)) for excluded_dir in excluded_dirs):
                        self.raw_recommendations['directories'].add(dir_path)
                for file_path in service_exclusions['files']:
                    if file_path not in excluded_files:
                        self.raw_recommendations['files'].add(file_path)
            
            self.formatted_recommendations = ExclusionAggregator.format_aggregated_exclusions(
                ExclusionAggregator.aggregate_exclusions(self.raw_recommendations)
            )
            
            logger.debug(f"Formatted recommendations:\n{self.formatted_recommendations}")
        
        return self.raw_recommendations

    def get_formatted_recommendations(self) -> str:
        if self.formatted_recommendations is None:
            self.get_grouped_recommendations({})
        return self.formatted_recommendations

    def check_for_new_exclusions(self, current_settings: Dict[str, List[str]]) -> bool:
        raw_recommendations = self.get_grouped_recommendations(current_settings)
        excluded_dirs = set(current_settings.get('excluded_dirs', []))
        excluded_files = set(current_settings.get('excluded_files', []))

        new_dirs = raw_recommendations['directories'] - excluded_dirs
        new_files = raw_recommendations['files'] - excluded_files

        return bool(new_dirs or new_files)