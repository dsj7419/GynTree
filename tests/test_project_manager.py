"""
GynTree: This file contains unit tests for the ProjectManager class,
ensuring proper project creation, saving, and loading functionality.
"""

import pytest
import os
from services.ProjectManager import ProjectManager
from models.Project import Project

@pytest.fixture
def project_manager():
    return ProjectManager()

def test_create_and_load_project(tmpdir, project_manager):
    project = Project(
        name="test_project",
        start_directory=str(tmpdir),
        excluded_dirs=["node_modules"],
        excluded_files=[".env"]
    )
    
    project_manager.save_project(project)
    
    project_file = os.path.join('config', 'projects', 'test_project.json')
    assert os.path.exists(project_file)
    
    loaded_project = project_manager.load_project("test_project")
    
    assert loaded_project.name == "test_project"
    assert loaded_project.start_directory == str(tmpdir)
    assert loaded_project.excluded_dirs == ["node_modules"]
    assert loaded_project.excluded_files == [".env"]

def test_load_nonexistent_project(project_manager):
    project = project_manager.load_project("nonexistent_project")
    assert project is None

def test_update_existing_project(tmpdir, project_manager):
    project = Project(
        name="update_test",
        start_directory=str(tmpdir),
        excluded_dirs=["old_dir"],
        excluded_files=["old_file"]
    )
    project_manager.save_project(project)

    project.excluded_dirs = ["new_dir"]
    project.excluded_files = ["new_file"]
    project_manager.save_project(project)

    loaded_project = project_manager.load_project("update_test")
    assert loaded_project.excluded_dirs == ["new_dir"]
    assert loaded_project.excluded_files == ["new_file"]

def test_list_projects(project_manager):
    projects = [
        Project(name="project1", start_directory="/path1", excluded_dirs=[], excluded_files=[]),
        Project(name="project2", start_directory="/path2", excluded_dirs=[], excluded_files=[])
    ]
    for project in projects:
        project_manager.save_project(project)

    project_list = project_manager.list_projects()
    assert "project1" in project_list
    assert "project2" in project_list

def test_delete_project(project_manager):
    project = Project(name="to_delete", start_directory="/path", excluded_dirs=[], excluded_files=[])
    project_manager.save_project(project)

    assert project_manager.delete_project("to_delete")
    assert not project_manager.load_project("to_delete")

def test_project_name_validation(project_manager):
    with pytest.raises(ValueError):
        Project(name="invalid/name", start_directory="/path", excluded_dirs=[], excluded_files=[])

def test_project_directory_validation(project_manager):
    with pytest.raises(ValueError):
        Project(name="valid_name", start_directory="nonexistent/path", excluded_dirs=[], excluded_files=[])