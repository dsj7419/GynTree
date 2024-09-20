from typing import List, Set
from services.ExclusionService import ExclusionService
from services.ProjectTypeDetector import ProjectTypeDetector
from services.SettingsManager import SettingsManager
from services.auto_exclude.IDEandGitAutoExclude import IDEandGitAutoExclude
from services.auto_exclude.PythonAutoExclude import PythonAutoExclude
from services.auto_exclude.WebAutoExclude import WebAutoExclude
from services.auto_exclude.JavaScriptNodeJsAutoExclude import JavaScriptNodeJsAutoExclude
from services.auto_exclude.DatabaseAutoExclude import DatabaseAutoExclude

class ExclusionServiceFactory:
    @staticmethod
    def create_services(project_types: Set[str], start_directory: str, project_type_detector: ProjectTypeDetector, settings_manager: SettingsManager) -> List[ExclusionService]:
        services = [IDEandGitAutoExclude(start_directory, project_type_detector, settings_manager)]

        service_map = {
            'python': PythonAutoExclude,
            'web': WebAutoExclude,
            'javascript': JavaScriptNodeJsAutoExclude,
            'database': DatabaseAutoExclude,
            'nextjs': WebAutoExclude
        }

        for project_type in project_types:
            service_class = service_map.get(project_type.lower())
            if service_class:
                services.append(service_class(start_directory, project_type_detector, settings_manager))

        return services