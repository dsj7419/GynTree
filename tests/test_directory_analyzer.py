import os
import pytest
import threading
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.SettingsManager import SettingsManager
from models.Project import Project

@pytest.fixture
def mock_project(tmpdir):
    return Project(
        name="test_project",
        start_directory=str(tmpdir),
        root_exclusions=[],
        excluded_dirs=[],
        excluded_files=[]
    )

@pytest.fixture
def settings_manager(mock_project):
    return SettingsManager(mock_project)

@pytest.fixture
def analyzer(mock_project, settings_manager):
    return DirectoryAnalyzer(mock_project.start_directory, settings_manager)

def test_directory_analysis(tmpdir, analyzer):
    test_file = tmpdir.join("test_file.py")
    test_file.write("# gyntree: Test purpose.")
    result = analyzer.analyze_directory()
    # Navigate through the nested structure
    def find_file(structure, target_path):
        if structure['type'] == 'file' and structure['path'] == str(test_file):
            return structure
        elif 'children' in structure:
            for child in structure['children']:
                found = find_file(child, target_path)
                if found:
                    return found
        return None
    file_info = find_file(result, str(test_file))
    assert file_info is not None
    assert file_info['description'] == "This is a test purpose."

def test_excluded_directory(tmpdir, mock_project, settings_manager):
    excluded_dir = tmpdir.mkdir("excluded")
    excluded_file = excluded_dir.join("excluded_file.py")
    excluded_file.write("# This should not be analyzed")
    mock_project.excluded_dirs = [str(excluded_dir)]
    settings_manager.update_settings({'excluded_dirs': [str(excluded_dir)]})
    analyzer = DirectoryAnalyzer(str(tmpdir), settings_manager)
    result = analyzer.analyze_directory()
    assert str(excluded_file) not in result

def test_excluded_file(tmpdir, mock_project, settings_manager):
    test_file = tmpdir.join("excluded_file.py")
    test_file.write("# This should not be analyzed")
    mock_project.excluded_files = [str(test_file)]
    settings_manager.update_settings({'excluded_files': [str(test_file)]})
    analyzer = DirectoryAnalyzer(str(tmpdir), settings_manager)
    result = analyzer.analyze_directory()
    assert str(test_file) not in result

def test_nested_directory_analysis(tmpdir, analyzer):
    nested_dir = tmpdir.mkdir("nested")
    nested_file = nested_dir.join("nested_file.py")
    nested_file.write("# gyntree: This is a nested file")
    result = analyzer.analyze_directory()
    assert str(nested_file) in result
    assert result[str(nested_file)]['description'] == "This is a nested file"

def test_get_flat_structure(tmpdir, analyzer):
    tmpdir.join("file1.py").write("# gyntree: File 1")
    tmpdir.join("file2.py").write("# gyntree: File 2")
    flat_structure = analyzer.get_flat_structure()
    assert len(flat_structure) == 2
    assert any(item['path'].endswith('file1.py') for item in flat_structure)
    assert any(item['path'].endswith('file2.py') for item in flat_structure)

def test_empty_directory(tmpdir, analyzer):
    result = analyzer.analyze_directory()
    # Check that the 'children' list is empty
    assert result['children'] == []

def test_large_directory_structure(tmpdir, analyzer):
    for i in range(1000):
        tmpdir.join(f"file_{i}.py").write(f"# gyntree: File {i}")
    result = analyzer.analyze_directory()
    assert len(result) == 1000

def test_stop_analysis(tmpdir, analyzer):
    for i in range(1000):
        tmpdir.join(f"file_{i}.py").write(f"# gyntree: File {i}")
    
    def stop_analysis():
        analyzer.stop()
    
    timer = threading.Timer(0.1, stop_analysis)
    timer.start()
    
    result = analyzer.analyze_directory()
    assert len(result) < 1000

def test_root_exclusions(tmpdir, mock_project, settings_manager):
    root_dir = tmpdir.mkdir("root_excluded")
    root_file = root_dir.join("root_file.py")
    root_file.write("# This should not be analyzed")
    mock_project.root_exclusions = [str(root_dir)]
    settings_manager.update_settings({'root_exclusions': [str(root_dir)]})
    analyzer = DirectoryAnalyzer(str(tmpdir), settings_manager)
    result = analyzer.analyze_directory()
    assert str(root_file) not in result

def test_symlink_handling(tmpdir, analyzer):
    real_dir = tmpdir.mkdir("real_dir")
    real_dir.join("real_file.py").write("# gyntree: real file")
    symlink_dir = tmpdir.join("symlink_dir")
    target = str(real_dir)
    link_name = str(symlink_dir)

    if hasattr(os, 'symlink'):
        try:
            os.symlink(target, link_name)
        except (OSError, NotImplementedError, AttributeError):
            pytest.skip("Symlink not supported on this platform or insufficient permissions")
    else:
        pytest.skip("Symlink not supported on this platform")

    result = analyzer.analyze_directory()
    assert any('real_file.py' in path for path in result.keys())
    assert len([path for path in result.keys() if 'real_file.py' in path]) == 1