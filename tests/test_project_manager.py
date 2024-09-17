import pytest
import os
from services.ProjectManager import ProjectManager
from models.Project import Project

def test_create_and_load_project(tmpdir):
    project_manager = ProjectManager()

    # Create a new project
    project = Project(
        name="test_project",
        start_directory=str(tmpdir),
        excluded_dirs=["node_modules"],
        excluded_files=[".env"]
    )
    
    # Save the project
    project_manager.save_project(project)
    
    # Ensure the project file exists
    project_file = os.path.join('config', 'projects', 'test_project.json')
    assert os.path.exists(project_file)
    
    # Load the project
    loaded_project = project_manager.load_project("test_project")
    
    # Ensure the project is loaded correctly
    assert loaded_project.name == "test_project"
    assert loaded_project.start_directory == str(tmpdir)
    assert loaded_project.excluded_dirs == ["node_modules"]
    assert loaded_project.excluded_files == [".env"]

def test_load_nonexistent_project():
    project_manager = ProjectManager()
    
    # Try to load a project that doesn't exist
    project = project_manager.load_project("nonexistent_project")
    
    assert project is None
