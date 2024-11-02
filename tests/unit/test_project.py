import pytest
import os
from pathlib import Path
from models.Project import Project
import logging

logger = logging.getLogger(__name__)
pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]

class TestProject:
    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing"""
        test_dir = tmp_path / "project_test_dir"
        test_dir.mkdir(parents=True, exist_ok=True)
        return str(test_dir)

    def test_project_initialization(self, temp_dir):
        """Test basic project initialization with valid data"""
        project = Project(
            name="test_project",
            start_directory=temp_dir,
            root_exclusions=["node_modules"],
            excluded_dirs=["dist"],
            excluded_files=[".env"]
        )
        
        assert project.name == "test_project"
        assert project.start_directory == temp_dir
        assert project.root_exclusions == ["node_modules"]
        assert project.excluded_dirs == ["dist"]
        assert project.excluded_files == [".env"]

    def test_project_initialization_with_defaults(self, temp_dir):
        """Test project initialization with default values"""
        project = Project(name="test_project", start_directory=temp_dir)
        
        assert project.name == "test_project"
        assert project.start_directory == temp_dir
        assert project.root_exclusions == []
        assert project.excluded_dirs == []
        assert project.excluded_files == []

    def test_project_name_validation_invalid_chars(self, temp_dir):
        """Test project name validation with invalid characters"""
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        
        for char in invalid_chars:
            with pytest.raises(ValueError, match=f"Invalid project name:"):
                Project(name=f"test{char}project", start_directory=temp_dir)

    def test_project_name_validation_valid(self, temp_dir):
        """Test project name validation with valid characters"""
        valid_names = [
            "test_project",
            "test-project",
            "TestProject123",
            "test.project",
            "test project"
        ]
        
        for name in valid_names:
            project = Project(name=name, start_directory=temp_dir)
            assert project.name == name

    def test_project_directory_validation(self, tmp_path):
        """Test project directory validation"""
        non_existent_path = tmp_path / "definitely_does_not_exist"
        with pytest.raises(ValueError, match="Directory does not exist:"):
            Project(
                name="test_project",
                start_directory=str(non_existent_path)
            )

    def test_project_serialization(self, temp_dir):
        """Test project serialization to dictionary"""
        project = Project(
            name="test_project",
            start_directory=temp_dir,
            root_exclusions=["node_modules"],
            excluded_dirs=["dist"],
            excluded_files=[".env"]
        )
        
        data = project.to_dict()
        assert data == {
            'name': "test_project",
            'start_directory': temp_dir,
            'root_exclusions': ["node_modules"],
            'excluded_dirs': ["dist"],
            'excluded_files': [".env"]
        }

    def test_project_deserialization(self, temp_dir):
        """Test project deserialization from dictionary"""
        data = {
            'name': "test_project",
            'start_directory': temp_dir,
            'root_exclusions': ["node_modules"],
            'excluded_dirs': ["dist"],
            'excluded_files': [".env"]
        }
        
        project = Project.from_dict(data)
        assert project.name == data['name']
        assert project.start_directory == data['start_directory']
        assert project.root_exclusions == data['root_exclusions']
        assert project.excluded_dirs == data['excluded_dirs']
        assert project.excluded_files == data['excluded_files']

    def test_project_deserialization_with_missing_fields(self, temp_dir):
        """Test project deserialization with missing optional fields"""
        data = {
            'name': "test_project",
            'start_directory': temp_dir
        }
        
        project = Project.from_dict(data)
        assert project.name == "test_project"
        assert project.start_directory == temp_dir
        assert project.root_exclusions == []
        assert project.excluded_dirs == []
        assert project.excluded_files == []

    def test_project_with_relative_path(self, temp_dir):
        """Test project with relative directory path"""
        # Create a subdirectory in temp_dir for testing relative paths
        test_subdir = Path(temp_dir) / "test_subdir"
        test_subdir.mkdir(parents=True, exist_ok=True)
        
        # Use the parent as current directory to create a relative path
        current_dir = Path(temp_dir)
        relative_path = os.path.join(".", "test_subdir")
        
        # Change to the temp directory temporarily
        original_dir = os.getcwd()
        os.chdir(str(current_dir))
        try:
            project = Project(name="test_project", start_directory=relative_path)
            assert os.path.basename(project.start_directory) == "test_subdir"
        finally:
            os.chdir(original_dir)