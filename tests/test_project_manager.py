import pytest
import os
import json
from services.ProjectManager import ProjectManager
from models.Project import Project

@pytest.fixture
def project_manager(tmpdir):
    ProjectManager.projects_dir = str(tmpdir.mkdir("projects"))
    return ProjectManager()

def test_create_and_load_project(project_manager):
    project = Project(
        name="test_project",
        start_directory="/test/path",
        root_exclusions=["node_modules"],
        excluded_dirs=["dist"],
        excluded_files=[".env"]
    )
    project_manager.save_project(project)
    
    project_file = os.path.join(ProjectManager.projects_dir, 'test_project.json')
    assert os.path.exists(project_file)
    
    loaded_project = project_manager.load_project("test_project")
    assert loaded_project.name == "test_project"
    assert loaded_project.start_directory == "/test/path"
    assert loaded_project.root_exclusions == ["node_modules"]
    assert loaded_project.excluded_dirs == ["dist"]
    assert loaded_project.excluded_files == [".env"]

def test_load_nonexistent_project(project_manager):
    project = project_manager.load_project("nonexistent_project")
    assert project is None

def test_update_existing_project(project_manager):
    project = Project(
        name="update_test",
        start_directory="/old/path",
        root_exclusions=["old_root"],
        excluded_dirs=["old_dir"],
        excluded_files=["old_file"]
    )
    project_manager.save_project(project)
    
    project.start_directory = "/new/path"
    project.root_exclusions = ["new_root"]
    project.excluded_dirs = ["new_dir"]
    project.excluded_files = ["new_file"]
    project_manager.save_project(project)
    
    loaded_project = project_manager.load_project("update_test")
    assert loaded_project.start_directory == "/new/path"
    assert loaded_project.root_exclusions == ["new_root"]
    assert loaded_project.excluded_dirs == ["new_dir"]
    assert loaded_project.excluded_files == ["new_file"]

def test_list_projects(project_manager):
    projects = [
        Project(name="project1", start_directory="/path1"),
        Project(name="project2", start_directory="/path2")
    ]
    for project in projects:
        project_manager.save_project(project)
    
    project_list = project_manager.list_projects()
    assert "project1" in project_list
    assert "project2" in project_list

def test_delete_project(project_manager):
    project = Project(name="to_delete", start_directory="/path")
    project_manager.save_project(project)
    
    assert project_manager.delete_project("to_delete")
    assert project_manager.load_project("to_delete") is None

def test_project_name_validation(project_manager):
    with pytest.raises(ValueError):
        Project(name="invalid/name", start_directory="/path")

def test_project_directory_validation(project_manager):
    with pytest.raises(ValueError):
        Project(name="valid_name", start_directory="nonexistent/path")

def test_save_project_with_custom_settings(project_manager):
    project = Project(
        name="custom_settings",
        start_directory="/custom/path",
        root_exclusions=["custom_root"],
        excluded_dirs=["custom_dir"],
        excluded_files=["custom_file"]
    )
    project_manager.save_project(project)
    
    with open(os.path.join(ProjectManager.projects_dir, 'custom_settings.json'), 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data['name'] == "custom_settings"
    assert saved_data['start_directory'] == "/custom/path"
    assert saved_data['root_exclusions'] == ["custom_root"]
    assert saved_data['excluded_dirs'] == ["custom_dir"]
    assert saved_data['excluded_files'] == ["custom_file"]

def test_load_project_with_missing_fields(project_manager):
    incomplete_project_data = {
        'name': 'incomplete_project',
        'start_directory': '/incomplete/path'
    }
    with open(os.path.join(ProjectManager.projects_dir, 'incomplete_project.json'), 'w') as f:
        json.dump(incomplete_project_data, f)
    
    loaded_project = project_manager.load_project('incomplete_project')
    assert loaded_project.name == 'incomplete_project'
    assert loaded_project.start_directory == '/incomplete/path'
    assert loaded_project.root_exclusions == []
    assert loaded_project.excluded_dirs == []
    assert loaded_project.excluded_files == []

def test_cleanup(project_manager):
    project_manager.cleanup()