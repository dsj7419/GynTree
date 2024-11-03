import logging
import os
from typing import Dict, Set

from services.ExclusionService import ExclusionService
from services.ProjectTypeDetector import ProjectTypeDetector
from services.SettingsManager import SettingsManager

logger = logging.getLogger(__name__)


class WebAutoExclude(ExclusionService):
    def __init__(
        self,
        start_directory: str,
        project_type_detector: ProjectTypeDetector,
        settings_manager: SettingsManager,
    ):
        super().__init__(start_directory, project_type_detector, settings_manager)

    def get_exclusions(self) -> Dict[str, Set[str]]:
        recommendations = {
            "root_exclusions": set(),
            "excluded_dirs": set(),
            "excluded_files": set(),
        }

        if (
            self.project_type_detector.detect_web_project()
            or self.project_type_detector.detect_nextjs_project()
        ):
            recommendations["root_exclusions"].update(
                [".cache", ".tmp", "dist", "build"]
            )
            recommendations["excluded_dirs"].add("public")
            logger.debug("WebAutoExclude: Adding web-related excluded_dirs")

        for root, dirs, files in self.walk_directory():
            if "public" in dirs:
                recommendations["excluded_dirs"].add(
                    os.path.relpath(os.path.join(root, "public"), self.start_directory)
                )
                logger.debug(
                    "WebAutoExclude: Recommending exclusion of 'public' directory"
                )

            for file in files:
                if file.endswith(
                    (
                        ".ico",
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".gif",
                        ".svg",
                        ".webp",
                        ".bmp",
                        ".tiff",
                    )
                ):
                    file_path = os.path.relpath(
                        os.path.join(root, file), self.start_directory
                    )
                    recommendations["excluded_files"].add(file_path)
                    logger.debug(
                        f"WebAutoExclude: Recommending exclusion of asset file {file_path}"
                    )
                elif file in ["robots.txt", "sitemap.xml", "favicon.ico"]:
                    file_path = os.path.relpath(
                        os.path.join(root, file), self.start_directory
                    )
                    recommendations["excluded_files"].add(file_path)
                    logger.debug(
                        f"WebAutoExclude: Recommending exclusion of web-related file {file_path}"
                    )

        return recommendations
