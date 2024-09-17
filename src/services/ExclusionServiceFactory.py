from typing import List, Type
from services.ExclusionService import ExclusionService
from services.auto_exclude.PythonAutoExclude import PythonAutoExclude
from services.auto_exclude.IDEandGitAutoExclude import IDEandGitAutoExclude
from services.auto_exclude.DatabaseAutoExclude import DatabaseAutoExclude
from services.auto_exclude.NextJsNodeJsAutoExclude import NextJsNodeJsAutoExclude
from services.auto_exclude.WebAutoExclude import WebAutoExclude

class ExclusionServiceFactory:
    @staticmethod
    def create_services(project_types: set, start_directory: str) -> List[ExclusionService]:
        services = [IDEandGitAutoExclude(start_directory)]  # Always include IDE and Git exclusions
        
        service_map = {
            'python': PythonAutoExclude,
            'web': WebAutoExclude,
            'nextjs': NextJsNodeJsAutoExclude,
            'database': DatabaseAutoExclude
        }
        
        for project_type in project_types:
            if project_type in service_map:
                services.append(service_map[project_type](start_directory))
        
        return services