"""
Module for managing resource paths across different environments.
Handles both development and production (PyInstaller) environments.
"""

import os
import sys
from pathlib import Path
from typing import Optional

class ResourcePathManager:
    """
    Manages resource paths across different environments (dev/production).
    
    Attributes:
        _base_path (Path): Base path for resource resolution
        
    Properties:
        base_path (Path): Read-only access to base path
    """
    
    def __init__(self) -> None:
        """Initialize the resource path manager."""
        self._base_path: Path = self._determine_base_path()
        
    def _determine_base_path(self) -> Path:
        """
        Determine the base path for resources.
        
        Returns:
            Path: Base path for resource resolution
            
        Notes:
            - Checks for PyInstaller bundle first
            - Falls back to project root directory
        """
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
        Get absolute path to resource, works both for development and PyInstaller bundles.
        
        Args:
            relative_path: Path relative to either src or root directory
            
        Returns:
            str: Absolute path to the resource
            
        Raises:
            FileNotFoundError: If resource cannot be found
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
        """Get the base path for resource resolution."""
        return self._base_path

# Global instance
_manager = ResourcePathManager()

def get_resource_path(relative_path: str) -> str:
    """
    Global function to get resource path.
    
    Args:
        relative_path: Path relative to either src or root directory
        
    Returns:
        str: Absolute path to the resource
        
    Raises:
        FileNotFoundError: If resource cannot be found
    """
    return _manager.get_resource_path(relative_path)