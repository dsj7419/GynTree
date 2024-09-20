import os
from typing import Dict, Set
from services.ExclusionService import ExclusionService
from services.ProjectTypeDetector import ProjectTypeDetector
from services.SettingsManager import SettingsManager
import logging

logger = logging.getLogger(__name__)

class DatabaseAutoExclude(ExclusionService):
    def __init__(self, start_directory: str, project_type_detector: ProjectTypeDetector, settings_manager: SettingsManager):
        super().__init__(start_directory, project_type_detector, settings_manager)

    def get_exclusions(self) -> Dict[str, Set[str]]:
        recommendations = {'root_exclusions': set(), 'excluded_dirs': set(), 'excluded_files': set()}

        if self.project_type_detector.detect_database_project():
            recommendations['root_exclusions'].add('prisma')
            logger.debug("DatabaseAutoExclude: Adding 'prisma' to root exclusions")

        for root, dirs, files in self.walk_directory():
            if 'prisma' in dirs:
                prisma_dir = os.path.join(root, 'prisma')
                migrations_dir = os.path.join(prisma_dir, 'migrations')
                if os.path.isdir(migrations_dir):
                    recommendations['excluded_dirs'].add(os.path.relpath(migrations_dir, self.start_directory))
                    logger.debug(f"DatabaseAutoExclude: Recommending exclusion of migrations directory {migrations_dir}")

                schema_path = os.path.join(prisma_dir, 'schema.prisma')
                if os.path.exists(schema_path):
                    recommendations['excluded_files'].add(os.path.relpath(schema_path, self.start_directory))
                    logger.debug(f"DatabaseAutoExclude: Recommending exclusion of schema file {schema_path}")

            for file in files:
                if file.endswith(('.sqlite', '.db', '.sqlite3', '.db3', '.sql')):
                    full_path = os.path.join(root, file)
                    recommendations['excluded_files'].add(os.path.relpath(full_path, self.start_directory))
                    logger.debug(f"DatabaseAutoExclude: Recommending exclusion of database file {full_path}")

        return recommendations