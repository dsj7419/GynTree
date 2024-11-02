import os
import sys

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    Handles both root-level resources (like assets) and src-level resources (like styles).
    """
    try:
        # If we're running as a PyInstaller bundle
        base_path = sys._MEIPASS
    except AttributeError:
        # If we're running in a normal Python environment
        # Get the directory containing the current file
        current_dir = os.path.dirname(__file__)
        # Go up to the src directory
        src_dir = os.path.dirname(current_dir)
        # Go up one more level to the root project directory
        root_dir = os.path.dirname(src_dir)
        
        # Check if the resource exists in src directory first
        src_path = os.path.join(src_dir, relative_path)
        if os.path.exists(src_path):
            return os.path.normpath(src_path)
        
        # If not found in src, look in root directory
        root_path = os.path.join(root_dir, relative_path)
        return os.path.normpath(root_path)
        
    # For PyInstaller bundle, just use the base path
    return os.path.normpath(os.path.join(base_path, relative_path))