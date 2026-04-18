import os
from abc import ABC, abstractmethod
from typing import Dict, Iterator, List, Set, Tuple

from services.ProjectTypeDetector import ProjectTypeDetector
from services.SettingsManager import SettingsManager


class ExclusionService(ABC):
    def __init__(
        self,
        start_directory: str,
        project_type_detector: ProjectTypeDetector,
        settings_manager: SettingsManager,
    ) -> None:
        self.start_directory = start_directory
        self.project_type_detector = project_type_detector
        self.settings_manager = settings_manager

    @abstractmethod
    def get_exclusions(self) -> Dict[str, Set[str]]:
        pass

    def get_relative_path(self, path: str) -> str:
        return os.path.relpath(path, self.start_directory)

    def should_exclude(self, path: str) -> bool:
        result: bool = self.settings_manager.is_excluded(path)
        return result

    def walk_directory(self) -> Iterator[Tuple[str, List[str], List[str]]]:
        for root, dirs, files in os.walk(self.start_directory):
            dirs[:] = [
                d for d in dirs if not self.should_exclude(os.path.join(root, d))
            ]
            yield root, dirs, files
