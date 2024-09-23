import os
import pytest
import threading
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.SettingsManager import SettingsManager
from models.Project import Project

pytestmark = pytest.mark.integration

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
    test_file.write("# GynTree: Test purpose.")
    result = analyzer.analyze_directory()

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
    assert file_info['description'] == "This is a Test purpose."

def test_excluded_directory(tmpdir, mock_project, settings_manager):
    excluded_dir = tmpdir.mkdir("excluded")
    excluded_file = excluded_dir.join("excluded_file.py")
    excluded_file.write("# Not analyzed")
    mock_project.excluded_dirs = [str(excluded_dir)]
    settings_manager.update_settings({'excluded_dirs': [str(excluded_dir)]})
    analyzer = DirectoryAnalyzer(str(tmpdir), settings_manager)
    result = analyzer.analyze_directory()
    assert str(excluded_file) not in str(result)

def test_excluded_file(tmpdir, mock_project, settings_manager):
    test_file = tmpdir.join("excluded_file.py")
    test_file.write("# Not analyzed")
    mock_project.excluded_files = [str(test_file)]
    settings_manager.update_settings({'excluded_files': [str(test_file)]})
    analyzer = DirectoryAnalyzer(str(tmpdir), settings_manager)
    result = analyzer.analyze_directory()
    assert str(test_file) not in str(result)

def test_nested_directory_analysis(tmpdir, analyzer):
    nested_dir = tmpdir.mkdir("nested")
    nested_file = nested_dir.join("nested_file.py")
    nested_file.write("# GynTree: Nested file")
    result = analyzer.analyze_directory()
    assert str(nested_file) in str(result)
    assert result[str(nested_file)]['description'] == "This is a Nested file"

def test_get_flat_structure(tmpdir, analyzer):
    tmpdir.join("file1.py").write("# GynTree: File 1")
    tmpdir.join("file2.py").write("# GynTree: File 2")
    flat_structure = analyzer.get_flat_structure()
    assert len(flat_structure) == 2
    assert any(item['path'].endswith('file1.py') for item in flat_structure)
    assert any(item['path'].endswith('file2.py') for item in flat_structure)

def test_empty_directory(tmpdir, analyzer):
    result = analyzer.analyze_directory()
    assert result['children'] == []

def test_large_directory_structure(tmpdir, analyzer):
    for i in range(1000):
        tmpdir.join(f"file_{i}.py").write(f"# GynTree: File {i}")
    result = analyzer.analyze_directory()
    assert len(result['children']) == 1000

def test_stop_analysis(tmpdir, analyzer):
    for i in range(1000):
        tmpdir.join(f"file_{i}.py").write(f"# GynTree: File {i}")

    def stop_analysis():
        analyzer.stop()

    timer = threading.Timer(0.1, stop_analysis)
    timer.start()
    result = analyzer.analyze_directory()
    assert len(result['children']) < 1000

def test_root_exclusions(tmpdir, mock_project, settings_manager):
    root_dir = tmpdir.mkdir("root_excluded")
    root_file = root_dir.join("root_file.py")
    root_file.write("# Not analyzed")
    mock_project.root_exclusions = [str(root_dir)]
    settings_manager.update_settings({'root_exclusions': [str(root_dir)]})
    analyzer = DirectoryAnalyzer(str(tmpdir), settings_manager)
    result = analyzer.analyze_directory()
    assert str(root_file) not in str(result)

def test_symlink_handling(tmpdir, analyzer):
    real_dir = tmpdir.mkdir("real_dir")
    real_dir.join("real_file.py").write("# GynTree: Real file")
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

@pytest.mark.slow
def test_large_nested_directory_structure(tmpdir, analyzer):
    def create_nested_structure(directory, depth, files_per_dir):
        if depth == 0:
            return
        for i in range(files_per_dir):
            directory.join(f"file_{i}.py").write(f"# GynTree: File {i} at depth {depth}")
        for i in range(3):  
            subdir = directory.mkdir(f"subdir_{i}")
            create_nested_structure(subdir, depth - 1, files_per_dir)

    create_nested_structure(tmpdir, depth=5, files_per_dir=10)
    result = analyzer.analyze_directory()
    
    def count_files(structure):
        count = len([child for child in structure['children'] if child['type'] == 'file'])
        for child in structure['children']:
            if child['type'] == 'directory':
                count += count_files(child)
        return count

    total_files = count_files(result)
    expected_files = 10 * (1 + 3 + 9 + 27 + 81)  # Sum of 10 * (3^0 + 3^1 + 3^2 + 3^3 + 3^4)
    assert total_files == expected_files

def test_file_type_detection(tmpdir, analyzer):
    tmpdir.join("python_file.py").write("# GynTree: Python file")
    tmpdir.join("javascript_file.js").write("// GynTree: JavaScript file")
    tmpdir.join("html_file.html").write("<!-- GynTree: HTML file -->")
    tmpdir.join("css_file.css").write("/* GynTree: CSS file */")
    
    result = analyzer.analyze_directory()
    
    file_types = {child['name']: child['type'] for child in result['children']}
    assert file_types['python_file.py'] == 'file'
    assert file_types['javascript_file.js'] == 'file'
    assert file_types['html_file.html'] == 'file'
    assert file_types['css_file.css'] == 'file'

def test_directory_permissions(tmpdir, analyzer):
    restricted_dir = tmpdir.mkdir("restricted")
    restricted_dir.join("secret.txt").write("Top secret")
    os.chmod(str(restricted_dir), 0o000)  # Remove all permissions
    
    try:
        result = analyzer.analyze_directory()
        assert "restricted" in [child['name'] for child in result['children']]
        assert len([child for child in result['children'] if child['name'] == "restricted"][0]['children']) == 0
    finally:
        os.chmod(str(restricted_dir), 0o755)  # Restore permissions for cleanup

def test_unicode_filenames(tmpdir, analyzer):
    unicode_filename = "üñíçödé_file.py"
    tmpdir.join(unicode_filename).write("# GynTree: Unicode filename test")
    
    result = analyzer.analyze_directory()
    assert unicode_filename in [child['name'] for child in result['children']]

def test_empty_files(tmpdir, analyzer):
    tmpdir.join("empty_file.py").write("")
    result = analyzer.analyze_directory()
    empty_file = [child for child in result['children'] if child['name'] == "empty_file.py"][0]
    assert empty_file['description'] == "No description available"

def test_non_utf8_files(tmpdir, analyzer):
    non_utf8_file = tmpdir.join("non_utf8.txt")
    with open(str(non_utf8_file), 'wb') as f:
        f.write(b'\xff\xfe' + "Some non-UTF8 content".encode('utf-16le'))
    
    result = analyzer.analyze_directory()
    assert "non_utf8.txt" in [child['name'] for child in result['children']]

def test_very_long_filenames(tmpdir, analyzer):
    long_filename = "a" * 255 + ".py"  
    tmpdir.join(long_filename).write("# GynTree: Very long filename test")
    
    result = analyzer.analyze_directory()
    assert long_filename in [child['name'] for child in result['children']]

@pytest.mark.slow
def test_performance_large_codebase(tmpdir, analyzer):
    for i in range(10000):  # Create 10,000 files
        tmpdir.join(f"file_{i}.py").write(f"# GynTree: File {i}\n" * 100)  # Each file has 100 lines
    
    import time
    start_time = time.time()
    result = analyzer.analyze_directory()
    end_time = time.time()
    
    assert len(result['children']) == 10000
    assert end_time - start_time < 60  # Ensure analysis completes in less than 60 seconds