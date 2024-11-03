import logging
import os
from typing import Dict, List, Set

from services.ExclusionService import ExclusionService
from services.ExclusionServiceFactory import ExclusionServiceFactory
from services.ProjectTypeDetector import ProjectTypeDetector
from services.SettingsManager import SettingsManager

logger = logging.getLogger(__name__)


class AutoExcludeManager:
    def __init__(
        self,
        start_directory: str,
        settings_manager: SettingsManager,
        project_types: Set[str],
        project_type_detector: ProjectTypeDetector,
    ):
        self.start_directory = os.path.abspath(start_directory)
        self.settings_manager = settings_manager
        self.project_types = project_types
        self.exclusion_services: List[
            ExclusionService
        ] = ExclusionServiceFactory.create_services(
            project_types, self.start_directory, project_type_detector, settings_manager
        )
        logger.debug(
            f"Created exclusion services: {[type(service).__name__ for service in self.exclusion_services]}"
        )
        self.raw_recommendations: Dict[str, Set[str]] = {
            "root_exclusions": set(),
            "excluded_dirs": set(),
            "excluded_files": set(),
        }

    def has_new_recommendations(self) -> bool:
        """
        Check if there are any new recommendations that haven't been applied.

        Returns:
            bool: True if there are new recommendations, False otherwise
        """
        recommendations = self.get_recommendations()
        has_new = any(len(items) > 0 for items in recommendations.values())
        logger.debug(f"Checking for new recommendations: {has_new}")
        return has_new

    def get_recommendations(self) -> Dict[str, Set[str]]:
        """Get new recommendations that aren't already in the settings."""
        self.raw_recommendations = {
            "root_exclusions": set(),
            "excluded_dirs": set(),
            "excluded_files": set(),
        }

        # Get current exclusions
        current_exclusions = {
            "root_exclusions": set(self.settings_manager.get_root_exclusions()),
            "excluded_dirs": set(self.settings_manager.get_excluded_dirs()),
            "excluded_files": set(self.settings_manager.get_excluded_files()),
        }

        # Collect all recommendations from services
        for service in self.exclusion_services:
            try:
                service_exclusions = service.get_exclusions()
                for category in ["root_exclusions", "excluded_dirs", "excluded_files"]:
                    self.raw_recommendations[category].update(
                        service_exclusions.get(category, set())
                    )
            except Exception as e:
                logger.error(
                    f"Error getting exclusions from service {type(service).__name__}: {str(e)}"
                )

        # Filter out already excluded items
        new_recommendations = {
            "root_exclusions": set(),
            "excluded_dirs": set(),
            "excluded_files": set(),
        }

        for category in ["root_exclusions", "excluded_dirs", "excluded_files"]:
            new_items = (
                self.raw_recommendations[category] - current_exclusions[category]
            )
            # Only include items that aren't already excluded and aren't in a path that's already excluded
            for item in new_items:
                full_path = os.path.join(self.start_directory, item)
                # Only add if not already excluded by another rule
                if not self.settings_manager.is_excluded(full_path):
                    new_recommendations[category].add(item)

        total_new = sum(len(items) for items in new_recommendations.values())
        logger.debug(f"Found {total_new} new recommendations")
        return new_recommendations

    def get_formatted_recommendations(self) -> str:
        """Format the recommendations for display."""
        recommendations = self.get_recommendations()
        lines = []

        for category in ["root_exclusions", "excluded_dirs", "excluded_files"]:
            if recommendations[category]:
                lines.append(f"{category.replace('_', ' ').title()}:")
                for path in sorted(recommendations[category]):
                    lines.append(f" - {path}")
                lines.append("")

        formatted = "\n".join(lines).rstrip()
        if not formatted:
            logger.debug("No new recommendations to format")
            return "No new exclusions to suggest."
        return formatted

    def apply_recommendations(self):
        """Apply the current recommendations to the settings."""
        try:
            recommendations = self.get_recommendations()
            if not any(recommendations.values()):
                logger.debug("No new recommendations to apply")
                return

            current_settings = self.settings_manager.settings

            for category in ["root_exclusions", "excluded_dirs", "excluded_files"]:
                current_set = set(current_settings.get(category, []))
                new_set = current_set | recommendations[category]
                current_settings[category] = sorted(list(new_set))

            self.settings_manager.update_settings(current_settings)
            logger.info("Successfully applied auto-exclude recommendations to settings")
        except Exception as e:
            logger.error(f"Error applying recommendations: {str(e)}")
            raise

    def get_combined_exclusions(self) -> Dict[str, Set[str]]:
        """Get current exclusions combined with new recommendations."""
        current = {
            "root_exclusions": set(self.settings_manager.get_root_exclusions()),
            "excluded_dirs": set(self.settings_manager.get_excluded_dirs()),
            "excluded_files": set(self.settings_manager.get_excluded_files()),
        }

        recommendations = self.get_recommendations()

        return {
            category: current[category] | recommendations[category]
            for category in current.keys()
        }
