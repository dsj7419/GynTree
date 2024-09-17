"""
GynTree: This file defines the DatabaseAutoExclude class, which identifies database-related files and directories for exclusion.
"""
import os
from services.ExclusionService import ExclusionService

class DatabaseAutoExclude(ExclusionService):
    def __init__(self, start_directory):
        super().__init__(start_directory)

    def get_exclusions(self):
        recommendations = {'directories': set(), 'files': set()}

        for root, dirs, files in os.walk(self.start_directory):
            if 'prisma' in dirs:
                prisma_dir = os.path.join(root, 'prisma')
                recommendations['directories'].add(os.path.join(prisma_dir, 'migrations'))
                
                for file in os.listdir(prisma_dir):
                    if file.endswith('.ts') or file.endswith('.js'):
                        recommendations['files'].add(os.path.join(prisma_dir, file))
                
                schema_path = os.path.join(prisma_dir, 'schema.prisma')
                if os.path.exists(schema_path):
                    recommendations['files'].add(schema_path)

            for file in files:
                if file.endswith('.sqlite') or file.endswith('.db'):
                    recommendations['files'].add(os.path.join(root, file))

        return recommendations