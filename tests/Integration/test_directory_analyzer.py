# tests/Integration/test_DirectoryAnalyzer.py
import os
import pytest
import threading
import logging
import gc
import psutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.SettingsManager import SettingsManager
from models.Project import Project

pytestmark = pytest.mark.integration

logger = logging.getLogger(__name__)

class DirectoryAnalyzerTestHelper:
    """Helper class for DirectoryAnalyzer testing"""
    def __init__(self, tmpdir: Path):
        self.tmpdir = tmpdir
        self.initial_memory = None

    def create_file_with_comment(self, path: str, comment: str) -> Path:
        """Create a file with a GynTree comment"""
        file_path = self.tmpdir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(f"# GynTree: {comment}")
        return file_path

    def create_nested_structure(self, depth: int, files_per_dir: int) -> None:
        """Create a nested directory structure"""
        def _create_nested(directory: Path, current_depth: int):
            if current_depth <= 0:
                return
            
            for i in range(files_per_dir):
                file_path = directory / f"file_{i}.py"
                self.create_file_with_comment(
                    str(file_path.relative_to(self.tmpdir)),
                    f"File {i} at depth {current_depth}")
            
            for i in range(3):
                subdir = directory / f"subdir_{i}"
                subdir.mkdir(exist_ok=True)
                _create_nested(subdir, current_depth - 1)
        
        _create_nested(self.tmpdir, depth)

    def track_memory(self) -> None:
        """Start memory tracking"""
        gc.collect()
        self.initial_memory = psutil.Process().memory_info().rss

    def check_memory_usage(self, operation: str) -> None:
        """Check memory usage after operation"""
        if self.initial_memory is not None:
            gc.collect()
            current_memory = psutil.Process().memory_info().rss
            memory_diff = current_memory - self.initial_memory
            if memory_diff > 50 * 1024 * 1024:  # 50MB threshold
                logger.warning(f"High memory usage after {operation}: {memory_diff / 1024 / 1024:.2f}MB")

@pytest.fixture
def helper(tmpdir):
    """Create test helper instance"""
    return DirectoryAnalyzerTestHelper(Path(tmpdir))

@pytest.fixture
def mock_project(helper):
    """Create mock project instance"""
    return Project(
        name="test_project",
        start_directory=str(helper.tmpdir),
        root_exclusions=[],
        excluded_dirs=[],
        excluded_files=[]
    )

@pytest.fixture
def settings_manager(mock_project):
    """Create SettingsManager instance"""
    return SettingsManager(mock_project)

@pytest.fixture
def analyzer(mock_project, settings_manager):
    """Create DirectoryAnalyzer instance with cleanup"""
    analyzer = DirectoryAnalyzer(mock_project.start_directory, settings_manager)
    yield analyzer
    analyzer.stop()
    gc.collect()

@pytest.mark.timeout(30)
def test_directory_analysis(helper, analyzer):
    """Test basic directory analysis"""
    helper.track_memory()
    
    test_file = helper.create_file_with_comment("test_file.py", "Test purpose")
    result = analyzer.analyze_directory()

    def find_file(structure: Dict[str, Any], target_path: str) -> Optional[Dict[str, Any]]:
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
    assert file_info['description'] == "Test purpose"
    
    helper.check_memory_usage("basic analysis")

@pytest.mark.timeout(30)
def test_excluded_directory(helper, mock_project, settings_manager):
    """Test excluded directory handling"""
    helper.track_memory()
    
    excluded_dir = helper.tmpdir / "excluded"
    excluded_dir.mkdir()
    excluded_file = helper.create_file_with_comment(
        "excluded/excluded_file.py",
        "Should not be analyzed"
    )
    
    mock_project.excluded_dirs = [str(excluded_dir)]
    settings_manager.update_settings({'excluded_dirs': [str(excluded_dir)]})
    
    analyzer = DirectoryAnalyzer(str(helper.tmpdir), settings_manager)
    result = analyzer.analyze_directory()
    
    assert str(excluded_file) not in str(result)
    
    helper.check_memory_usage("excluded directory")

@pytest.mark.timeout(30)
def test_excluded_file(helper, mock_project, settings_manager):
    """Test excluded file handling"""
    helper.track_memory()
    
    test_file = helper.create_file_with_comment(
        "excluded_file.py",
        "Should not be analyzed"
    )
    
    mock_project.excluded_files = [str(test_file)]
    settings_manager.update_settings({'excluded_files': [str(test_file)]})
    
    analyzer = DirectoryAnalyzer(str(helper.tmpdir), settings_manager)
    result = analyzer.analyze_directory()
    
    assert str(test_file) not in str(result)
    
    helper.check_memory_usage("excluded file")

@pytest.mark.timeout(30)
def test_nested_directory_analysis(helper, analyzer):
    """Test nested directory analysis"""
    helper.track_memory()
    
    nested_file = helper.create_file_with_comment(
        "nested/nested_file.py",
        "Nested file"
    )
    
    result = analyzer.analyze_directory()
    nested_path = str(nested_file).replace('\\', '/')
    assert any(nested_path in str(child['path']).replace('\\', '/') 
              for child in result['children'][0]['children'])
    
    helper.check_memory_usage("nested analysis")

@pytest.mark.timeout(30)
def test_get_flat_structure(helper, analyzer):
    """Test flat structure generation"""
    helper.track_memory()
    
    helper.create_file_with_comment("file1.py", "File 1")
    helper.create_file_with_comment("file2.py", "File 2")
    
    flat_structure = analyzer.get_flat_structure()
    assert len([f for f in flat_structure if 'styles' not in str(f['path'])]) == 2
    
    helper.check_memory_usage("flat structure")

@pytest.mark.timeout(30)
def test_empty_directory(helper, analyzer):
    """Test empty directory handling"""
    helper.track_memory()
    
    result = analyzer.analyze_directory()
    assert len([c for c in result['children'] if c['name'] != 'styles']) == 0
    
    helper.check_memory_usage("empty directory")

@pytest.mark.timeout(60)
def test_large_directory_structure(helper, analyzer):
    """Test large directory structure analysis"""
    helper.track_memory()
    
    # Clean directory but preserve styles folder
    if helper.tmpdir.exists():
        for item in Path(helper.tmpdir).glob('*'):
            if item.name != 'styles':
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        for subitem in item.glob('**/*'):
                            if subitem.is_file():
                                subitem.unlink()
                        item.rmdir()
                except:
                    pass
    
    # Create test files
    for i in range(1000):
        helper.create_file_with_comment(f"file_{i}.py", f"File {i}")
    
    # Analyze directory
    result = analyzer.analyze_directory()
    
    # Count only Python files to avoid styles directory
    py_files = [child for child in result['children'] 
                if child['name'].endswith('.py')]
    assert len(py_files) == 1000
    
    # Verify each expected file exists
    file_names = {f"file_{i}.py" for i in range(1000)}
    actual_names = {child['name'] for child in py_files}
    assert file_names == actual_names
    
    # Memory check and cleanup
    helper.check_memory_usage("large structure")
    analyzer.stop()
    
@pytest.mark.timeout(30)
def test_stop_analysis(helper, analyzer):
    """Test analysis stopping functionality"""
    helper.track_memory()
    
    for i in range(1000):
        helper.create_file_with_comment(f"file_{i}.py", f"File {i}")
    
    def stop_analysis():
        analyzer.stop()
    
    timer = threading.Timer(0.1, stop_analysis)
    timer.start()
    
    try:
        result = analyzer.analyze_directory()
        if result:  # Handle case where analysis was stopped before completion
            assert len([c for c in result.get('children', []) 
                       if c['name'] != 'styles']) < 1000
    finally:
        timer.cancel()
    
    helper.check_memory_usage("stop analysis")

@pytest.mark.timeout(30)
def test_root_exclusions(helper, mock_project, settings_manager):
    """Test root exclusions handling"""
    helper.track_memory()
    
    root_dir = helper.tmpdir / "root_excluded"
    root_dir.mkdir()
    root_file = helper.create_file_with_comment(
        "root_excluded/root_file.py",
        "Should not be analyzed"
    )
    
    mock_project.root_exclusions = [str(root_dir)]
    settings_manager.update_settings({'root_exclusions': [str(root_dir)]})
    
    analyzer = DirectoryAnalyzer(str(helper.tmpdir), settings_manager)
    result = analyzer.analyze_directory()
    
    assert str(root_file) not in str(result)
    
    helper.check_memory_usage("root exclusions")

@pytest.mark.timeout(30)
def test_symlink_handling(helper, analyzer):
    """Test symlink handling"""
    helper.track_memory()
    
    real_dir = helper.tmpdir / "real_dir"
    real_dir.mkdir()
    real_file = helper.create_file_with_comment("real_dir/real_file.py", "Real file")
    
    symlink_dir = helper.tmpdir / "symlink_dir"
    
    if hasattr(os, 'symlink'):
        try:
            os.symlink(str(real_dir), str(symlink_dir))
        except (OSError, NotImplementedError, AttributeError):
            pytest.skip("Symlink not supported on this platform or insufficient permissions")
    else:
        pytest.skip("Symlink not supported on this platform")

    result = analyzer.analyze_directory()
    assert any(str(real_file) in str(child['path']) 
              for child in result['children'][0]['children'])
    
    helper.check_memory_usage("symlink handling")

@pytest.mark.timeout(60)
@pytest.mark.slow
def test_large_nested_directory_structure(helper, analyzer):
    """Test large nested directory structure analysis"""
    helper.track_memory()
    
    helper.create_nested_structure(depth=5, files_per_dir=10)
    result = analyzer.analyze_directory()
    
    def count_files(structure: Dict[str, Any]) -> int:
        if not structure.get('children'):
            return 0
        count = len([child for child in structure['children']
                    if child['type'] == 'file' and 'styles' not in str(child['path'])])
        for child in structure['children']:
            if child['type'] == 'directory' and child['name'] != 'styles':
                count += count_files(child)
        return count
    
    total_files = count_files(result)
    expected_files = 10 * (1 + 3 + 9 + 27 + 81)  # Sum of 10 * (3^0 + 3^1 + 3^2 + 3^3 + 3^4)
    assert total_files == expected_files
    
    helper.check_memory_usage("large nested structure")

@pytest.mark.timeout(30)
def test_file_type_detection(helper, analyzer):
    """Test detection of different file types"""
    helper.track_memory()
    
    # Create files of different types
    files = {
        'python_file.py': '# GynTree: Python file',
        'javascript_file.js': '// GynTree: JavaScript file',
        'html_file.html': '<!-- GynTree: HTML file -->',
        'css_file.css': '/* GynTree: CSS file */'
    }
    
    for filename, content in files.items():
        (helper.tmpdir / filename).write_text(content)
    
    result = analyzer.analyze_directory()
    file_types = {child['name']: child['type'] 
                 for child in result['children']}
    
    for filename in files:
        assert file_types[filename] == 'file'
    
    helper.check_memory_usage("file type detection")

@pytest.mark.timeout(30)
def test_directory_permissions(helper, analyzer):
    """Test handling of restricted directory permissions"""
    helper.track_memory()
    
    restricted_dir = helper.tmpdir / "restricted"
    restricted_dir.mkdir()
    
    # Create the file before applying restrictions
    secret_file = helper.create_file_with_comment("restricted/secret.txt", "Top secret")
    
    # Set restrictive permissions
    try:
        os.chmod(str(restricted_dir), 0o000)
    except OSError:
        pytest.skip("Cannot modify directory permissions on this platform")
    
    try:
        result = analyzer.analyze_directory()
        
        # Verify directory exists in result
        assert "restricted" in [child['name'] for child in result['children']]
        
        restricted_children = [child for child in result['children']
                             if child['name'] == "restricted"][0]
        
        # Either the children list should be empty or files should be marked as inaccessible
        children = restricted_children.get('children', [])
        if children:
            for child in children:
                desc = child.get('description', '')
                assert desc in ['No description available', 'Unsupported file type'], \
                    f"File {child['name']} should be marked as inaccessible or unsupported"
    finally:
        try:
            os.chmod(str(restricted_dir), 0o755)
        except OSError:
            pass
    
    helper.check_memory_usage("permission handling")


@pytest.mark.timeout(30)
def test_unicode_filenames(helper, analyzer):
    """Test handling of Unicode filenames"""
    helper.track_memory()
    
    unicode_filename = "üñíçödé_file.py"
    helper.create_file_with_comment(unicode_filename, "Unicode filename test")
    
    result = analyzer.analyze_directory()
    assert unicode_filename in [child['name'] for child in result['children']]
    
    helper.check_memory_usage("unicode filenames")

@pytest.mark.timeout(30)
def test_empty_files(helper, analyzer):
    """Test handling of empty files"""
    helper.track_memory()
    
    empty_file = helper.tmpdir / "empty_file.py"
    empty_file.write_text("")
    
    result = analyzer.analyze_directory()
    empty_file_info = [child for child in result['children'] 
                      if child['name'] == "empty_file.py"][0]
    assert empty_file_info['description'] == "No description available"
    
    helper.check_memory_usage("empty files")

@pytest.mark.timeout(30)
def test_non_utf8_files(helper, analyzer):
    """Test handling of non-UTF8 files"""
    helper.track_memory()
    
    non_utf8_file = helper.tmpdir / "non_utf8.txt"
    with open(str(non_utf8_file), 'wb') as f:
        f.write(b'\xff\xfe' + "Some non-UTF8 content".encode('utf-16le'))
    
    result = analyzer.analyze_directory()
    assert "non_utf8.txt" in [child['name'] for child in result['children']]
    
    helper.check_memory_usage("non-utf8 files")

@pytest.mark.timeout(30)
def test_very_long_filenames(helper, analyzer):
    """Test handling of very long filenames"""
    helper.track_memory()
    
    # Use a shorter filename that won't exceed OS limits
    long_filename = "a" * 200 + ".py"  
    try:
        helper.create_file_with_comment(long_filename, "Very long filename test")
        
        result = analyzer.analyze_directory()
        assert long_filename in [child['name'] for child in result['children']]
    except OSError as e:
        if "name too long" in str(e).lower():
            pytest.skip("System does not support filenames this long")
        raise
    
    helper.check_memory_usage("long filenames")

@pytest.mark.timeout(120)
@pytest.mark.slow
def test_performance_large_codebase(helper, analyzer):
    """Test performance with large codebase"""
    helper.track_memory()
    
    for i in range(10000):
        content = f"# GynTree: File {i}\n" + "x = 1\n" * 99
        (helper.tmpdir / f"file_{i}.py").write_text(content)
    
    start_time = datetime.now()
    result = analyzer.analyze_directory()
    duration = (datetime.now() - start_time).total_seconds()
    
    assert len([c for c in result['children'] if c['name'] != 'styles']) == 10000
    assert duration < 60  # Should complete within 60 seconds
    
    helper.check_memory_usage("large codebase")

@pytest.mark.timeout(30)
def test_concurrent_analysis(helper, analyzer):
    """Test concurrent directory analysis"""
    helper.track_memory()
    
    # Create test structure
    for i in range(100):
        helper.create_file_with_comment(f"file_{i}.py", f"File {i}")
    
    # Run multiple analyses concurrently
    def run_analysis():
        return analyzer.analyze_directory()
    
    threads = [
        threading.Thread(target=run_analysis)
        for _ in range(3)
    ]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join(timeout=5.0)
        assert not thread.is_alive(), "Analysis thread timed out"
    
    helper.check_memory_usage("concurrent analysis")

@pytest.mark.timeout(30)
def test_error_recovery(helper, analyzer):
    """Test error recovery during analysis"""
    helper.track_memory()
    
    error_file = helper.tmpdir / "error_file.py"
    error_file.write_text("")  # Create empty file
    
    try:
        os.chmod(str(error_file), 0o000)
    except OSError:
        pytest.skip("Cannot modify file permissions on this platform")
    
    try:
        result = analyzer.analyze_directory()
        assert "error_file.py" in [child['name'] for child in result['children']]
        error_file_info = [child for child in result['children']
                          if child['name'] == "error_file.py"][0]
        assert "No description available" in error_file_info['description']
    finally:
        os.chmod(str(error_file), 0o644)
    
    helper.check_memory_usage("error recovery")

@pytest.mark.timeout(30)
def test_memory_cleanup(helper, analyzer):
    """Test memory cleanup during analysis"""
    helper.track_memory()
    
    for i in range(1000):
        helper.create_file_with_comment(f"file_{i}.py", f"File {i}")
    
    for _ in range(3):
        result = analyzer.analyze_directory()
        assert len([c for c in result['children'] if c['name'] != 'styles']) == 1000
        gc.collect()  # Force garbage collection between runs
    
    helper.check_memory_usage("memory cleanup")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])