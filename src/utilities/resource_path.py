import os
import sys
from pathlib import Path

class ResourcePathManager:
    """Manages resource paths across different environments (dev/production)"""
    
    def __init__(self):
        self._base_path = self._determine_base_path()
        
    def _determine_base_path(self) -> Path:
        """Determine the base path for resources"""
        try:
            # Check if running as PyInstaller bundle
            base_path = Path(sys._MEIPASS)
        except AttributeError:
            # Get the project root directory
            current_file = Path(__file__)
            # Go up two levels: utilities -> src -> project_root
            base_path = current_file.parent.parent.parent
            
        return base_path
    
    def get_resource_path(self, relative_path: str) -> str:
        """
        Get absolute path to resource, works both for:
        - Development
        - PyInstaller bundles
        """
        resource_path = self.base_path / relative_path
        
        # First check if resource exists in src directory
        src_path = self.base_path / 'src' / relative_path
        if src_path.exists():
            return str(src_path)
            
        # Then check in root directory
        if resource_path.exists():
            return str(resource_path)
            
        raise FileNotFoundError(f"Resource not found: {relative_path}")
    
    @property
    def base_path(self) -> Path:
        return self._base_path

# Global instance
_manager = ResourcePathManager()

def get_resource_path(relative_path: str) -> str:
    """Global function to get resource path"""
    return _manager.get_resource_path(relative_path)