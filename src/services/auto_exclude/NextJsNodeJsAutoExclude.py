"""
GynTree: This file defines the NextJsNodeJsAutoExclude class, which identifies Next.js and Node.js related directories for exclusion.
"""
import os
from services.ExclusionService import ExclusionService

class NextJsNodeJsAutoExclude(ExclusionService):
    def __init__(self, start_directory):
        super().__init__(start_directory)

    def get_exclusions(self):
        recommendations = {'directories': set(), 'files': set()}

        for root, dirs, _ in os.walk(self.start_directory):
            if '.next' in dirs:
                recommendations['directories'].add(os.path.join(root, '.next'))
            
            if 'node_modules' in dirs:
                recommendations['directories'].add(os.path.join(root, 'node_modules'))

            for dir in ['out', 'build', 'dist']:
                if dir in dirs:
                    recommendations['directories'].add(os.path.join(root, dir))

        return recommendations