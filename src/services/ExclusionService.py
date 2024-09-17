"""
GynTree: This file defines the base ExclusionService class for all exclusion services.
"""
from abc import ABC, abstractmethod
import os

class ExclusionService(ABC):
    def __init__(self, start_directory):
        self.start_directory = start_directory

    @abstractmethod
    def get_exclusions(self):
        pass

    def categorize_exclusions(self, exclusions):
        categorized = {'directories': {}, 'files': {}}
        for category, items in exclusions.items():
            for item in items:
                if self.is_directory(item):
                    categorized['directories'].setdefault(category, []).append(item)
                else:
                    categorized['files'].setdefault(category, []).append(item)
        return categorized

    def is_directory(self, path):
        return os.path.isdir(path)