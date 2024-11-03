import logging
import os
from typing import Dict, Set

from services.ExclusionService import ExclusionService
from services.ProjectTypeDetector import ProjectTypeDetector
from services.SettingsManager import SettingsManager

logger = logging.getLogger(__name__)


class PythonAutoExclude(ExclusionService):
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

        if self.project_type_detector.detect_python_project():
            python_root_exclusions = {
                "__pycache__",
                ".pytest_cache",
                "build",
                "dist",
                ".tox",
                "venv",
                ".venv",
                "env",
            }
            recommendations["root_exclusions"].update(python_root_exclusions)
            logger.debug(
                f"PythonAutoExclude: Adding Python-related excluded_dirs to root exclusions: {python_root_exclusions}"
            )

        for root, dirs, files in self.walk_directory():
            for file in files:
                if file.endswith((".pyc", ".pyo", ".coverage", ".egg-info")):
                    recommendations["excluded_files"].add(
                        os.path.relpath(os.path.join(root, file), self.start_directory)
                    )
                    logger.debug(
                        f"PythonAutoExclude: Recommending exclusion of Python-related file {file}"
                    )
                elif file in [
                    "requirements.txt",
                    "Pipfile",
                    "Pipfile.lock",
                    "poetry.lock",
                    "pyproject.toml",
                ]:
                    recommendations["excluded_files"].add(
                        os.path.relpath(os.path.join(root, file), self.start_directory)
                    )
                    logger.debug(
                        f"PythonAutoExclude: Recommending exclusion of Python dependency file {file}"
                    )

        setup_files = ["setup.py", "setup.cfg"]
        if any(
            os.path.exists(os.path.join(self.start_directory, f)) for f in setup_files
        ):
            recommendations["excluded_dirs"].update(["build", "dist"])
            logger.debug(
                "PythonAutoExclude: Recommending exclusion of 'build' and 'dist' excluded_dirs"
            )

        return recommendations
