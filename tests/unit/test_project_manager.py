import json
import logging
import os
from pathlib import Path

import pytest

from models.Project import Project
from services.ProjectManager import ProjectManager

pytestmark = pytest.mark.unit


class TestProjectManager:
    @pytest.fixture
    def test_dir(self, tmp_path):
        """Create a base test directory"""
        test_dir = tmp_path / "test_projects"
        test_dir.mkdir(parents=True, exist_ok=True)
        return test_dir

    @pytest.fixture
    def project_manager(self, test_dir):
        """Create ProjectManager instance with temporary directory"""
        ProjectManager.projects_dir = str(test_dir / "projects")
        return ProjectManager()

    @pytest.fixture
    def sample_project(self, test_dir):
        """Create a sample project for testing"""
        project_dir = test_dir / "test_directory"
        project_dir.mkdir(parents=True, exist_ok=True)
        return Project(
            name="test_project",
            start_directory=str(project_dir),
            root_exclusions=["node_modules"],
            excluded_dirs=["dist"],
            excluded_files=[".env"],
        )

    def test_projects_directory_creation(self, test_dir):
        """Test that projects directory is created on initialization"""
        projects_dir = test_dir / "projects_test"
        ProjectManager.projects_dir = str(projects_dir)
        ProjectManager()
        assert projects_dir.exists()
        assert projects_dir.is_dir()

    def test_projects_directory_creation_error(self, monkeypatch, test_dir):
        """Test error handling when projects directory creation fails"""
        # Set a non-existent directory path
        projects_dir = test_dir / "should_fail"
        ProjectManager.projects_dir = str(projects_dir)

        # Create mock that always raises PermissionError
        def mock_makedirs(*args, **kwargs):
            raise PermissionError("Permission denied")

        # Apply mock to os.makedirs
        monkeypatch.setattr(os, "makedirs", mock_makedirs)

        # Test that initialization fails
        with pytest.raises(PermissionError):
            ProjectManager()

    def test_save_project(self, project_manager, sample_project):
        """Test saving a project"""
        project_manager.save_project(sample_project)

        project_file = (
            Path(project_manager.projects_dir) / f"{sample_project.name}.json"
        )
        assert project_file.exists()

        with open(project_file) as f:
            data = json.load(f)
            assert data["name"] == sample_project.name
            assert data["start_directory"] == sample_project.start_directory
            assert data["root_exclusions"] == sample_project.root_exclusions
            assert data["excluded_dirs"] == sample_project.excluded_dirs
            assert data["excluded_files"] == sample_project.excluded_files

    def test_save_project_permission_error(
        self, project_manager, sample_project, monkeypatch
    ):
        """Test error handling when saving project fails due to permissions"""

        def mock_open(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr("builtins.open", mock_open)
        with pytest.raises(PermissionError):
            project_manager.save_project(sample_project)

    def test_load_project(self, project_manager, sample_project):
        """Test loading a project"""
        project_manager.save_project(sample_project)

        loaded_project = project_manager.load_project(sample_project.name)
        assert loaded_project is not None
        assert loaded_project.name == sample_project.name
        assert loaded_project.start_directory == sample_project.start_directory
        assert loaded_project.root_exclusions == sample_project.root_exclusions
        assert loaded_project.excluded_dirs == sample_project.excluded_dirs
        assert loaded_project.excluded_files == sample_project.excluded_files

    def test_load_project_json_error(self, project_manager, sample_project):
        """Test handling of corrupt JSON files"""
        # Create a corrupt JSON file
        project_file = (
            Path(project_manager.projects_dir) / f"{sample_project.name}.json"
        )
        project_file.parent.mkdir(parents=True, exist_ok=True)
        project_file.write_text("invalid json content")

        loaded_project = project_manager.load_project(sample_project.name)
        assert loaded_project is None

    def test_load_nonexistent_project(self, project_manager):
        """Test loading a project that doesn't exist"""
        loaded_project = project_manager.load_project("nonexistent_project")
        assert loaded_project is None

    def test_list_projects(self, project_manager, sample_project, test_dir):
        """Test listing all projects"""
        second_dir = test_dir / "second_directory"
        second_dir.mkdir(parents=True, exist_ok=True)

        second_project = Project(
            name="second_project",
            start_directory=str(second_dir),
            root_exclusions=["vendor"],
            excluded_dirs=["build"],
            excluded_files=["config.json"],
        )

        project_manager.save_project(sample_project)
        project_manager.save_project(second_project)

        project_list = project_manager.list_projects()
        assert len(project_list) == 2
        assert "test_project" in project_list
        assert "second_project" in project_list

    def test_list_projects_permission_error(self, project_manager, monkeypatch):
        """Test error handling when listing projects fails"""

        def mock_listdir(*args):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(os, "listdir", mock_listdir)
        project_list = project_manager.list_projects()
        assert project_list == []

    def test_delete_project(self, project_manager, sample_project):
        """Test deleting a project"""
        project_manager.save_project(sample_project)
        assert project_manager.delete_project(sample_project.name)

        project_file = (
            Path(project_manager.projects_dir) / f"{sample_project.name}.json"
        )
        assert not project_file.exists()
        assert sample_project.name not in project_manager.list_projects()

    def test_delete_project_permission_error(
        self, project_manager, sample_project, monkeypatch
    ):
        """Test error handling when deleting project fails"""
        project_manager.save_project(sample_project)

        def mock_remove(*args):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(os, "remove", mock_remove)
        assert not project_manager.delete_project(sample_project.name)

    def test_delete_nonexistent_project(self, project_manager):
        """Test deleting a project that doesn't exist"""
        assert not project_manager.delete_project("nonexistent_project")

    def test_save_and_update_project(self, project_manager, sample_project):
        """Test saving and then updating a project"""
        project_manager.save_project(sample_project)

        updated_project = Project(
            name=sample_project.name,
            start_directory=sample_project.start_directory,
            root_exclusions=sample_project.root_exclusions + ["vendor"],
            excluded_dirs=sample_project.excluded_dirs + ["build"],
            excluded_files=sample_project.excluded_files + ["config.json"],
        )
        project_manager.save_project(updated_project)

        loaded_project = project_manager.load_project(sample_project.name)
        assert loaded_project is not None
        assert loaded_project.root_exclusions == updated_project.root_exclusions
        assert loaded_project.excluded_dirs == updated_project.excluded_dirs
        assert loaded_project.excluded_files == updated_project.excluded_files

    def test_file_permissions(self, project_manager, sample_project, monkeypatch):
        """Test handling of file permission errors"""
        project_manager.save_project(sample_project)

        def selective_mock_open(*args, **kwargs):
            if "r" in kwargs.get("mode", args[1] if len(args) > 1 else ""):
                raise PermissionError("Permission denied")
            return open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", selective_mock_open)
        loaded_project = project_manager.load_project(sample_project.name)
        assert loaded_project is None
