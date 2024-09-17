import pytest
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.SettingsManager import SettingsManager
from models.Project import Project

def test_directory_analysis(tmpdir):
    test_dir = tmpdir.mkdir("test_dir")
    test_file = test_dir.join("test_file.py")
    test_file.write("# GynTree: Test purpose.")

    # Create a mock project
    project = Project(
        name="test_project",
        start_directory=str(test_dir),
        excluded_dirs=[],
        excluded_files=[]
    )

    # Initialize the SettingsManager with the mock project
    settings_manager = SettingsManager(project)

    analyzer = DirectoryAnalyzer(str(test_dir), settings_manager)
    result = analyzer.analyze_directory()

    assert str(test_file) in result
    assert result[str(test_file)] == "Test purpose."
