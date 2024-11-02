import os
from typing import Dict, Set
from pathlib import Path
from functools import lru_cache

class ProjectTypeDetector:
    """Detects project types based on file patterns and directory structure."""
    
    def __init__(self, start_directory: str):
        self.start_directory = start_directory
        self._file_cache: Dict[str, bool] = {}

    def _cache_key(self, extensions: Set[str]) -> str:
        """Create a stable cache key from a set of extensions"""
        return ','.join(sorted(extensions))

    def _has_file_with_extensions(self, extensions: Set[str]) -> bool:
        """
        Check if directory contains files with given extensions.
        Uses memory-efficient walk and caching.
        """
        cache_key = self._cache_key(extensions)
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]

        for root, _, files in os.walk(self.start_directory):
            for file in files:
                if any(file.lower().endswith(ext.lower()) for ext in extensions):
                    self._file_cache[cache_key] = True
                    return True
        
        self._file_cache[cache_key] = False
        return False

    def _has_files(self, filenames: Set[str]) -> bool:
        """
        Check if directory contains specific files.
        Case-insensitive comparison.
        """
        for root, _, files in os.walk(self.start_directory):
            files_lower = {f.lower() for f in files}
            if any(fname.lower() in files_lower for fname in filenames):
                return True
        return False

    def detect_python_project(self) -> bool:
        """Detect Python project by looking for .py files"""
        return self._has_file_with_extensions({'.py'})

    def detect_web_project(self) -> bool:
        """Detect web project by looking for web-related files"""
        web_extensions = {'.html', '.css', '.js', '.ts', '.jsx', '.tsx'}
        return self._has_file_with_extensions(web_extensions)

    def detect_javascript_project(self) -> bool:
        """Detect JavaScript/TypeScript project"""
        js_extensions = {'.js', '.ts', '.jsx', '.tsx'}
        js_config_files = {'package.json', 'tsconfig.json', '.eslintrc.js', '.eslintrc.json'}
        
        return (self._has_file_with_extensions(js_extensions) or 
                self._has_files(js_config_files))

    def detect_nextjs_project(self) -> bool:
        """Detect Next.js project using multiple indicators"""
        # Check for next.config.js
        if self._has_files({'next.config.js'}):
            return True
            
        # Check for package.json with Next.js dependency
        if os.path.exists(os.path.join(self.start_directory, 'package.json')):
            try:
                with open(os.path.join(self.start_directory, 'package.json'), 'r') as f:
                    if 'next' in f.read().lower():
                        return True
            except (IOError, UnicodeDecodeError):
                pass

        # Check for Next.js directory structure
        nextjs_indicators = {'pages', 'components'}
        return all(
            os.path.exists(os.path.join(self.start_directory, ind))
            for ind in nextjs_indicators
        )

    def detect_database_project(self) -> bool:
        """Detect database project by looking for database-related files"""
        db_indicators = {'prisma', 'schema.prisma', 'migrations', '.sqlite', '.db'}
        
        # Check directory contents
        contents = set()
        for root, dirs, files in os.walk(self.start_directory):
            contents.update(map(str.lower, files))
            contents.update(map(str.lower, dirs))
            
        return any(ind.lower() in contents for ind in db_indicators)

    def detect_project_types(self) -> Dict[str, bool]:
        """
        Detect all project types.
        Returns a dictionary mapping project types to boolean detection results.
        """
        return {
            'python': self.detect_python_project(),
            'web': self.detect_web_project(),
            'javascript': self.detect_javascript_project(),
            'nextjs': self.detect_nextjs_project(),
            'database': self.detect_database_project(),
        }