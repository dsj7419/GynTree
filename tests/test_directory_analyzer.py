"""
GynTree: This file contains unit tests for the DirectoryAnalyzer class,
verifying its ability to analyze directory structures and apply exclusion rules.
"""

import pytest
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.SettingsManager import SettingsManager
from models.Project import Project

@pytest.fixture
def mock_project(tmpdir):
    return Project(
        name="test_project",
        start_directory=str(tmpdir),
        excluded_dirs=[],
        excluded_files=[]
    )

@pytest.fixture
def analyzer(mock_project):
    settings_manager = SettingsManager(mock_project)
    return DirectoryAnalyzer(mock_project.start_directory, settings_manager)

def test_directory_analysis(tmpdir, analyzer):
    test_file = tmpdir.join("test_file.py")
    test_file.write("# GynTree: Test purpose.")

    result = analyzer.analyze_directory()

    assert str(test_file) in result
    assert result[str(test_file)]['description'] == "Test purpose."

def test_excluded_directory(tmpdir, mock_project):
    excluded_dir = tmpdir.mkdir("excluded")
    excluded_file = excluded_dir.join("excluded_file.py")
    excluded_file.write("# Should not be analyzed")

    mock_project.excluded_dirs = [str(excluded_dir)]
    settings_manager = SettingsManager(mock_project)
    analyzer = DirectoryAnalyzer(str(tmpdir), settings_manager)

    result = analyzer.analyze_directory()

    assert str(excluded_file) not in result

def test_excluded_file(tmpdir, mock_project):
    test_file = tmpdir.join("excluded_file.py")
    test_file.write("# Should not be analyzed")

    mock_project.excluded_files = [str(test_file)]
    settings_manager = SettingsManager(mock_project)
    analyzer = DirectoryAnalyzer(str(tmpdir), settings_manager)

    result = analyzer.analyze_directory()

    assert str(test_file) not in result

def test_nested_directory_analysis(tmpdir, analyzer):
    nested_dir = tmpdir.mkdir("nested")
    nested_file = nested_dir.join("nested_file.py")
    nested_file.write("# GynTree: Nested file")

    result = analyzer.analyze_directory()

    assert str(nested_file) in result
    assert result[str(nested_file)]['description'] == "Nested file"

def test_get_flat_structure(tmpdir, analyzer):
    tmpdir.join("file1.py").write("# GynTree: File 1")
    tmpdir.join("file2.py").write("# GynTree: File 2")

    flat_structure = analyzer.get_flat_structure()

    assert len(flat_structure) == 2
    assert any(item['path'].endswith('file1.py') for item in flat_structure)
    assert any(item['path'].endswith('file2.py') for item in flat_structure)

def test_empty_directory(tmpdir, analyzer):
    result = analyzer.analyze_directory()
    assert len(result) == 0

def test_large_directory_structure(tmpdir, analyzer):
    for i in range(1000):
        tmpdir.join(f"file_{i}.py").write(f"# GynTree: File {i}")

    result = analyzer.analyze_directory()
    assert len(result) == 1000