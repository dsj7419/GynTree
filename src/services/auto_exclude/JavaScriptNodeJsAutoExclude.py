import logging
import os
from typing import Dict, Set

from services.ExclusionService import ExclusionService
from services.ProjectTypeDetector import ProjectTypeDetector
from services.SettingsManager import SettingsManager

logger = logging.getLogger(__name__)


class JavaScriptNodeJsAutoExclude(ExclusionService):
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
            self.project_type_detector.detect_javascript_project()
            or self.project_type_detector.detect_nextjs_project()
        ):
            root_exclusions = {
                "node_modules",
                ".next",
                "dist",
                "build",
                "out",
                ".cache",
                ".tmp",
            }
            recommendations["root_exclusions"].update(root_exclusions)
            logger.debug(
                f"JavaScriptNodeJsAutoExclude: Adding JavaScript/Node.js related excluded_dirs to root exclusions: {root_exclusions}"
            )

            file_exclusions = {
                ".npmrc",
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
                ".eslintrc.js",
                ".eslintrc.cjs",
                "prettier.config.js",
                "next.config.js",
                "next-env.d.ts",
                "postcss.config.js",
                "postcss.config.cjs",
                "tailwind.config.js",
                "tailwind.config.ts",
                "tsconfig.json",
                ".babelrc",
                ".browserslistrc",
                "package.json",
            }
            recommendations["excluded_files"].update(file_exclusions)
            logger.debug(
                f"JavaScriptNodeJsAutoExclude: Recommending JavaScript/Node.js related files for exclusion: {file_exclusions}"
            )

        for root, dirs, files in self.walk_directory():
            for file in files:
                if file.endswith((".min.js", ".min.css")):
                    full_path = os.path.join(root, file)
                    recommendations["excluded_files"].add(
                        os.path.relpath(full_path, self.start_directory)
                    )
                    logger.debug(
                        f"JavaScriptNodeJsAutoExclude: Recommending exclusion of minified file {full_path}"
                    )

        return recommendations
