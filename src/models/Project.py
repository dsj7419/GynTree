# GynTree: This file defines the Project class. It stores project details like name, start directory, and excluded directories or files.

class Project:
    def __init__(self, name, start_directory, excluded_dirs=None, excluded_files=None):
        self.name = name
        self.start_directory = start_directory
        self.excluded_dirs = excluded_dirs if excluded_dirs is not None else []
        self.excluded_files = excluded_files if excluded_files is not None else []

    def to_dict(self):
        """Convert project details to a dictionary."""
        return {
            'name': self.name,
            'start_directory': self.start_directory,
            'excluded_dirs': self.excluded_dirs,
            'excluded_files': self.excluded_files
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Project instance from a dictionary."""
        return cls(
            name=data.get('name'),
            start_directory=data.get('start_directory'),
            excluded_dirs=data.get('excluded_dirs', []),
            excluded_files=data.get('excluded_files', [])
        )
