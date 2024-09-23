import os
from typing import Dict

class ProjectTypeDetector:
    def __init__(self, start_directory: str):
        self.start_directory = start_directory

    def detect_python_project(self) -> bool:
        for root, dirs, files in os.walk(self.start_directory):
            if any(file.endswith('.py') for file in files):
                return True
        return False

    def detect_web_project(self) -> bool:
        web_files = ['.html', '.css', '.js', '.ts', '.jsx', '.tsx']
        return any(any(file.endswith(ext) for ext in web_files) for file in os.listdir(self.start_directory))

    def detect_javascript_project(self) -> bool:
        js_files = ['.js', '.ts', '.jsx', '.tsx']
        js_config_files = ['package.json', 'tsconfig.json', '.eslintrc.js', '.eslintrc.json']
        return any(
            any(file.endswith(ext) for ext in js_files) or
            file in js_config_files
            for file in os.listdir(self.start_directory)
        )

    def detect_nextjs_project(self) -> bool:
        nextjs_indicators = ['next.config.js', 'pages', 'components']
        return (
            os.path.exists(os.path.join(self.start_directory, 'next.config.js')) or
            (os.path.exists(os.path.join(self.start_directory, 'package.json')) and
             'next' in open(os.path.join(self.start_directory, 'package.json')).read()) or
            all(os.path.exists(os.path.join(self.start_directory, ind)) for ind in nextjs_indicators)
        )

    def detect_database_project(self) -> bool:
        db_indicators = ['prisma', 'schema.prisma', 'migrations', '.sqlite', '.db']
        return any(indicator in os.listdir(self.start_directory) for indicator in db_indicators)

    def detect_project_types(self) -> Dict[str, bool]:
        return {
            'python': self.detect_python_project(),
            'web': self.detect_web_project(),
            'javascript': self.detect_javascript_project(),
            'nextjs': self.detect_nextjs_project(),
            'database': self.detect_database_project(),
        }