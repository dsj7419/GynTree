import pytest
import os
import json
from services.ProjectManager import ProjectManager
from models.Project import Project

pytestmark = pytest.mark.unit

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

def test_project_serialization(project_manager):
    project = Project(
        name="serialization_test",
        start_directory="/test/path",
        root_exclusions=["node_modules"],
        excluded_dirs=["dist"],
        excluded_files=[".env"]
    )
    serialized = project.to_dict()
    assert serialized['name'] == "serialization_test"
    assert serialized['start_directory'] == "/test/path"
    assert serialized['root_exclusions'] == ["node_modules"]
    assert serialized['excluded_dirs'] == ["dist"]
    assert serialized['excluded_files'] == [".env"]

def test_project_deserialization(project_manager):
    data = {
        'name': 'deserialization_test',
        'start_directory': '/test/path',
        'root_exclusions': ['node_modules'],
        'excluded_dirs': ['dist'],
        'excluded_files': ['.env']
    }
    project = Project.from_dict(data)
    assert project.name == 'deserialization_test'
    assert project.start_directory == '/test/path'
    assert project.root_exclusions == ['node_modules']
    assert project.excluded_dirs == ['dist']
    assert project.excluded_files == ['.env']

def test_save_and_load_multiple_projects(project_manager):
    projects = [
        Project(name="project1", start_directory="/path1"),
        Project(name="project2", start_directory="/path2"),
        Project(name="project3", start_directory="/path3")
    ]
    for project in projects:
        project_manager.save_project(project)
    
    loaded_projects = [project_manager.load_project(p.name) for p in projects]
    assert all(loaded is not None for loaded in loaded_projects)
    assert [p.name for p in loaded_projects] == ["project1", "project2", "project3"]

def test_project_file_integrity(project_manager):
    project = Project(
        name="integrity_test",
        start_directory="/test/path",
        root_exclusions=["node_modules"],
        excluded_dirs=["dist"],
        excluded_files=[".env"]
    )
    project_manager.save_project(project)
    
    file_path = os.path.join(ProjectManager.projects_dir, 'integrity_test.json')
    with open(file_path, 'r') as f:
        file_content = json.load(f)
    
    assert file_content['name'] == "integrity_test"
    assert file_content['start_directory'] == "/test/path"
    assert file_content['root_exclusions'] == ["node_modules"]
    assert file_content['excluded_dirs'] == ["dist"]
    assert file_content['excluded_files'] == [".env"]

def test_project_overwrite(project_manager):
    project = Project(name="overwrite_test", start_directory="/old/path")
    project_manager.save_project(project)
    
    updated_project = Project(name="overwrite_test", start_directory="/new/path")
    project_manager.save_project(updated_project)
    
    loaded_project = project_manager.load_project("overwrite_test")
    assert loaded_project.start_directory == "/new/path"

def test_invalid_project_name_characters(project_manager):
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        with pytest.raises(ValueError):
            Project(name=f"invalid{char}name", start_directory="/path")

def test_empty_project_name(project_manager):
    with pytest.raises(ValueError):
        Project(name="", start_directory="/path")

def test_project_name_whitespace(project_manager):
    with pytest.raises(ValueError):
        Project(name="  ", start_directory="/path")

def test_project_name_too_long(project_manager):
    with pytest.raises(ValueError):
        Project(name="a" * 256, start_directory="/path") 