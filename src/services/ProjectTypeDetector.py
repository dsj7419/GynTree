import os

class ProjectTypeDetector:
    def __init__(self, start_directory: str):
        self.start_directory = start_directory

    def detect_python_project(self) -> bool:
        python_indicators = ['.py', 'requirements.txt', 'setup.py', 'pyproject.toml']
        return any(
            any(file.endswith(indicator) for indicator in python_indicators)
            for file in os.listdir(self.start_directory)
        )

    def detect_web_project(self) -> bool:
        web_files = ['.html', '.css', '.js', '.ts', '.jsx', '.tsx']
        return any(any(file.endswith(ext) for ext in web_files) for file in os.listdir(self.start_directory))

    def detect_nextjs_project(self) -> bool:
        return os.path.exists(os.path.join(self.start_directory, 'next.config.js')) or \
               (os.path.exists(os.path.join(self.start_directory, 'package.json')) and \
               'next' in open(os.path.join(self.start_directory, 'package.json')).read())

    def detect_database_project(self) -> bool:
        db_indicators = ['prisma', 'schema.prisma', 'migrations', '.sqlite', '.db']
        return any(indicator in os.listdir(self.start_directory) for indicator in db_indicators)

    def detect_project_types(self) -> set:
        project_types = set()
        if self.detect_python_project():
            project_types.add('python')
        if self.detect_web_project():
            project_types.add('web')
        if self.detect_nextjs_project():
            project_types.add('nextjs')
        if self.detect_database_project():
            project_types.add('database')
        return project_types