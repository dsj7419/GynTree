class Project:
    def __init__(self, name, start_directory, root_exclusions=None, excluded_dirs=None, excluded_files=None):
        if not self.is_valid_name(name):
            raise ValueError(f"Invalid project name: {name}")
        self.name = name
        self.start_directory = start_directory
        self.root_exclusions = root_exclusions if root_exclusions is not None else []
        self.excluded_dirs = excluded_dirs if excluded_dirs is not None else []
        self.excluded_files = excluded_files if excluded_files is not None else []

    def to_dict(self):
        """Convert project details to a dictionary."""
        return {
            'name': self.name,
            'start_directory': self.start_directory,
            'root_exclusions': self.root_exclusions,
            'excluded_dirs': self.excluded_dirs,
            'excluded_files': self.excluded_files
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Project instance from a dictionary."""
        return cls(
            name=data.get('name'),
            start_directory=data.get('start_directory'),
            root_exclusions=data.get('root_exclusions', []),
            excluded_dirs=data.get('excluded_dirs', []),
            excluded_files=data.get('excluded_files', [])
        )
    
    @staticmethod
    def is_valid_name(name):
        invalid_chars = set('/\\:*?"<>|')
        return not any(char in invalid_chars for char in name)
