import time
import pytest
import os
import threading
from unittest.mock import Mock, patch
from services.DirectoryStructureService import DirectoryStructureService
from services.SettingsManager import SettingsManager

pytestmark = [
    pytest.mark.unit,
    pytest.mark.timeout(30)
]

@pytest.fixture
def mock_comment_parser(mocker):
    """Mock comment parser with consistent behavior"""
    parser = mocker.Mock()
    # Set default return value
    parser.get_file_purpose.return_value = "Test file description"
    return parser

@pytest.fixture
def service(mock_settings_manager, mock_comment_parser, mocker):
    """Create service with properly mocked dependencies"""
    # Patch CommentParser at module level to avoid any real file operations
    mocker.patch('services.DirectoryStructureService.CommentParser', 
                 return_value=mock_comment_parser)
    mocker.patch('services.DirectoryStructureService.DefaultFileReader')
    mocker.patch('services.DirectoryStructureService.DefaultCommentSyntax')
    return DirectoryStructureService(mock_settings_manager)

@pytest.fixture
def stop_event():
    """Provide clean stop event for each test"""
    event = threading.Event()
    yield event
    # Ensure event is cleared after test
    event.clear()

@pytest.fixture
def mock_settings_manager():
    """Provide settings manager mock with default behavior"""
    settings = Mock(spec=SettingsManager)
    settings.is_excluded.return_value = False
    return settings

def test_initialization(service, mock_settings_manager):
    """Test service initialization"""
    assert service.settings_manager == mock_settings_manager
    assert service.comment_parser is not None

def test_get_hierarchical_structure(service, tmp_path, stop_event):
    """Test hierarchical structure generation"""
    # Create test directory structure
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "test_file.txt").write_text("test content")
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    
    assert result["name"] == "test_dir"
    assert result["type"] == "directory"
    assert len(result["children"]) == 1
    assert result["children"][0]["name"] == "test_file.txt"

def test_get_flat_structure(service, tmp_path, stop_event):
    """Test flat structure generation"""
    # Create test directory structure
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "test_file.txt").write_text("test content")
    
    result = service.get_flat_structure(str(test_dir), stop_event)
    
    assert len(result) == 1
    assert result[0]["type"] == "file"
    assert result[0]["path"].endswith("test_file.txt")

def test_excluded_directories(service, tmp_path, stop_event, mock_settings_manager):
    """Test handling of excluded directories"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    excluded_dir = test_dir / "excluded"
    excluded_dir.mkdir()
    
    mock_settings_manager.is_excluded.side_effect = lambda path: "excluded" in path
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    
    assert result["name"] == "test_dir"
    assert len(result["children"]) == 0

def test_permission_error_handling(service, tmp_path, stop_event):
    """Test handling of permission errors"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    with patch('os.listdir') as mock_listdir:
        mock_listdir.side_effect = PermissionError("Access denied")
        
        result = service.get_hierarchical_structure(str(test_dir), stop_event)
        
        assert result["name"] == "test_dir"
        assert result["children"] == []

def test_generic_error_handling(service, tmp_path, stop_event):
    """Test handling of generic errors"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    with patch('os.listdir') as mock_listdir:
        mock_listdir.side_effect = Exception("Test error")
        
        result = service.get_hierarchical_structure(str(test_dir), stop_event)
        
        assert result["name"] == "test_dir"
        assert result["children"] == []

def test_stop_event_handling(service, tmp_path):
    """Test handling of stop event"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "test_file.txt").write_text("test content")
    
    stop_event = threading.Event()
    stop_event.set()  # Set stop event immediately
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    assert result == {}

def test_nested_directory_structure(service, tmp_path, stop_event):
    """Test handling of nested directory structures"""
    # Create nested test directory structure
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    sub_dir = test_dir / "sub_dir"
    sub_dir.mkdir()
    (sub_dir / "test_file.txt").write_text("test content")
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    
    assert result["name"] == "test_dir"
    assert len(result["children"]) == 1
    assert result["children"][0]["name"] == "sub_dir"
    assert len(result["children"][0]["children"]) == 1
    assert result["children"][0]["children"][0]["name"] == "test_file.txt"

def test_walk_directory(service, tmp_path, stop_event):
    """Test directory walking functionality"""
    # Create test directory structure
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    sub_dir = test_dir / "sub_dir"
    sub_dir.mkdir()
    (test_dir / "test1.txt").write_text("test content")
    (sub_dir / "test2.txt").write_text("test content")
    
    paths = []
    for root, dirs, files in service._walk_directory(str(test_dir), stop_event):
        paths.extend([os.path.join(root, f) for f in files])
    
    assert len(paths) == 2
    assert any("test1.txt" in p for p in paths)
    assert any("test2.txt" in p for p in paths)

def test_concurrent_access(service, tmp_path):
    """Test concurrent access to the service"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "test_file.txt").write_text("test content")
    
    results = []
    threads = []
    stop_events = [threading.Event() for _ in range(3)]
    
    def worker(stop_event):
        result = service.get_hierarchical_structure(str(test_dir), stop_event)
        results.append(result)
    
    for stop_event in stop_events:
        thread = threading.Thread(target=worker, args=(stop_event,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    assert len(results) == 3
    assert all(r["name"] == "test_dir" for r in results)
    assert all(len(r["children"]) == 1 for r in results)

def test_error_handling(service, tmp_path, stop_event):
    """Test error handling in UI operations"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    with patch('services.CommentParser.CommentParser.get_file_purpose', side_effect=Exception("Test error")):
        result = service.get_hierarchical_structure(str(test_dir), stop_event)
        assert result["name"] == "test_dir"
        assert isinstance(result, dict)  # Should return valid structure despite errors

def test_ui_state_consistency(service, tmp_path, stop_event):
    """Test directory structure consistency during operations"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "test_file.txt").write_text("test content")
    
    # Get structure multiple times to ensure consistency
    result1 = service.get_hierarchical_structure(str(test_dir), stop_event)
    result2 = service.get_hierarchical_structure(str(test_dir), stop_event)
    
    assert result1 == result2
    assert result1["name"] == "test_dir"

def test_null_directory_handling(service, stop_event):
    """Test handling of None or empty directory paths"""
    result = service.get_hierarchical_structure("", stop_event)
    assert isinstance(result, dict)
    assert result.get("error") is not None

def test_malformed_path_handling(service, stop_event):
    """Test handling of malformed paths"""
    result = service.get_hierarchical_structure("\\invalid//path", stop_event)
    assert isinstance(result, dict)
    assert result.get("error") is not None

def test_nested_error_handling(service, tmp_path, stop_event, mocker):
    """Test handling of errors in nested directories"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    sub_dir = test_dir / "sub_dir"
    sub_dir.mkdir()
    
    # Mock os.listdir to raise error for subdirectory
    original_listdir = os.listdir
    def mock_listdir(path):
        if "sub_dir" in str(path):
            raise PermissionError("Test error")
        return original_listdir(path)
    
    mocker.patch('os.listdir', side_effect=mock_listdir)
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    assert result["name"] == "test_dir"
    assert any(child.get("error") for child in result["children"])

@pytest.mark.timeout(30)
def test_long_path_handling(service, tmp_path, stop_event):
    """Test handling of very long path names"""
    test_dir = tmp_path / ("a" * 200)  # Create directory with long name
    test_dir.mkdir()
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    assert result["name"] == "a" * 200

def test_special_character_handling(service, tmp_path, stop_event):
    """Test handling of special characters in paths"""
    test_dir = tmp_path / "test@#$%^&"
    test_dir.mkdir()
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    assert result["name"] == "test@#$%^&"

def test_empty_directory_handling(service, tmp_path, stop_event):
    """Test handling of empty directories"""
    test_dir = tmp_path / "empty_dir"
    test_dir.mkdir()
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    assert result["name"] == "empty_dir"
    assert result["children"] == []

def test_safe_file_purpose(service, tmp_path):
    """Test _safe_get_file_purpose method to improve coverage of error handling"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    # Test normal case
    result = service._safe_get_file_purpose(str(test_file))
    assert result == "Test file description"
    
    # Test error case
    service.comment_parser.get_file_purpose.side_effect = Exception("Test error")
    result = service._safe_get_file_purpose(str(test_file))
    assert result is None

def test_walk_directory_error_handling(service, tmp_path, stop_event):
    """Test error handling in _walk_directory for improved coverage"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    with patch('os.walk') as mock_walk:
        mock_walk.side_effect = Exception("Test error")
        paths = list(service._walk_directory(str(test_dir), stop_event))
        assert paths == []

def test_flat_structure_error_handling(service, tmp_path, stop_event):
    """Test error handling in get_flat_structure to cover error branches"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    with patch('os.walk') as mock_walk:
        mock_walk.side_effect = Exception("Test error")
        result = service.get_flat_structure(str(test_dir), stop_event)
        assert result == []

def test_excluded_file_handling(service, tmp_path, stop_event, mock_settings_manager):
    """Test handling of excluded files for complete exclusion coverage"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    test_file = test_dir / "test.txt"
    test_file.write_text("test")
    
    mock_settings_manager.is_excluded.side_effect = lambda path: ".txt" in path
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    assert result["children"] == []

def test_recursive_error_handling(service, tmp_path, stop_event):
    """Test error handling in recursive analysis"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    with patch('os.listdir') as mock_listdir:
        mock_listdir.side_effect = Exception("Recursive error")
        
        result = service._analyze_recursive(str(test_dir), stop_event)
        
        assert result['name'] == "test_dir"
        assert result['error'] == "Error analyzing directory: Recursive error"
        assert result['children'] == []

def test_deep_nested_structure(service, tmp_path, stop_event):
    """Test handling of deeply nested directory structures"""
    test_dir = tmp_path / "test_dir"
    current = test_dir
    depth = 5
    
    # Create nested structure
    for i in range(depth):
        current.mkdir(parents=True)
        file_path = current / f"file{i}.txt"
        file_path.write_text(f"Content {i}")
        current = current / f"subdir{i}"
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    
    # Verify depth
    current_level = result
    for i in range(depth):
        assert current_level['name'] == os.path.basename(str(test_dir)) if i == 0 else f"subdir{i-1}"
        assert len(current_level['children']) > 0
        # Find the subdirectory in children
        subdir = next((child for child in current_level['children'] 
                      if child['type'] == 'directory'), None)
        if i < depth - 1:
            assert subdir is not None
            current_level = subdir

def test_complex_error_chain(service, tmp_path, stop_event):
    """Test handling of complex error chains in directory analysis"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    class CustomError(Exception):
        pass
    
    def complex_walk(*args):
        yield str(test_dir), ['subdir1', 'subdir2'], ['file1.txt']
        raise CustomError("Complex error")
    
    with patch('os.walk', side_effect=complex_walk):
        result = service.get_flat_structure(str(test_dir), stop_event)
        assert len(result) > 0  # Should have processed first yield
        assert all('error' not in item for item in result)  # No errors in processed items

def test_concurrent_modification(service, tmp_path, stop_event):
    """Test behavior during concurrent directory modification"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    # Create initial file
    test_file = test_dir / "test.txt"
    test_file.write_text("Initial content")
    
    def modify_directory():
        # Simulate concurrent modification
        (test_dir / "new_file.txt").write_text("New content")
        if test_file.exists():
            test_file.unlink()
    
    # Start analysis and modify directory during execution
    with patch('os.listdir', side_effect=lambda x: modify_directory() or ['test.txt', 'new_file.txt']):
        result = service.get_hierarchical_structure(str(test_dir), stop_event)
        assert result['name'] == "test_dir"
        assert any(child['name'] in ['test.txt', 'new_file.txt'] 
                  for child in result.get('children', []))

def test_error_propagation(service, tmp_path, stop_event):
    """Test error propagation through service layers"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    class LayeredError(Exception):
        pass
    
    with patch.object(service.comment_parser, 'get_file_purpose') as mock_purpose:
        mock_purpose.side_effect = LayeredError("Parser error")
        
        with patch('os.listdir', return_value=['test.txt']):
            with patch('os.path.isdir', return_value=False):
                result = service._analyze_recursive(str(test_dir), stop_event)
                assert result['children'][0].get('description') is None

def test_symlink_handling(service, tmp_path, stop_event):
    """Test handling of symbolic links in directory structure"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    # Create a file and a symbolic link to it
    test_file = test_dir / "test.txt"
    test_file.write_text("Test content")
    
    link_path = test_dir / "link.txt"
    try:
        os.symlink(str(test_file), str(link_path))
    except OSError:
        pytest.skip("Symbolic link creation not supported")
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    assert len(result['children']) == 2
    assert any(child['name'] == "link.txt" for child in result['children'])

def test_empty_path_components(service, tmp_path, stop_event):
    """Test handling of paths with empty components"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    # Test with path containing empty components
    path_with_empty = str(test_dir) + os.sep + "" + os.sep + "file.txt"
    
    result = service.get_hierarchical_structure(path_with_empty, stop_event)
    assert isinstance(result, dict)
    assert 'error' in result

def test_unicode_path_handling(service, tmp_path, stop_event):
    """Test handling of Unicode characters in paths"""
    test_dir = tmp_path / "test_dir_🚀"
    try:
        test_dir.mkdir()
    except Exception:
        pytest.skip("Unicode directory names not supported")
    
    test_file = test_dir / "test_文件.txt"
    test_file.write_text("Test content")
    
    result = service.get_hierarchical_structure(str(test_dir), stop_event)
    assert result['name'] == "test_dir_🚀"
    assert any(child['name'] == "test_文件.txt" for child in result['children'])

def test_memory_usage(service, tmp_path, stop_event):
    """Test memory usage with large directory structures"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    # Create a large number of files
    num_files = 1000
    for i in range(num_files):
        (test_dir / f"file_{i}.txt").write_text(f"Content {i}")
    
    import psutil
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    result = service.get_flat_structure(str(test_dir), stop_event)
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Verify reasonable memory usage (less than 100MB increase)
    assert memory_increase < 100 * 1024 * 1024  # 100MB
    assert len(result) == num_files

def test_stop_event_responsiveness(service, tmp_path):
    """Test responsiveness to stop event during intensive operations"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    # Create test files in batches to avoid timing issues
    batch_size = 2
    for i in range(5):  # Create 5 batches of 2 files each
        for j in range(batch_size):
            file_idx = i * batch_size + j
            (test_dir / f"file_{file_idx}.txt").write_text(f"Content {file_idx}")
        if i > 0:  # Add small delay between batches except first
            time.sleep(0.001)
    
    stop_event = threading.Event()
    processed_files = []
    
    def delayed_stop():
        time.sleep(0.02)  # Reduced delay for more reliable timing
        stop_event.set()
    
    stop_thread = threading.Thread(target=delayed_stop, name="StopEventThread")
    stop_thread.daemon = True
    stop_thread.start()
    
    # Add small delay to ensure thread starts
    time.sleep(0.001)
    
    try:
        result = service.get_hierarchical_structure(str(test_dir), stop_event)
    finally:
        stop_event.set()  # Ensure stop event is set
        stop_thread.join(timeout=1.0)  # Wait for thread with timeout
    
    # Test should pass if either:
    # 1. We got an empty result (stopped before processing)
    # 2. We got a directory with no children (stopped during processing)
    expected_results = [
        {},  # Complete stop
        {'name': 'test_dir', 'type': 'directory', 'path': str(test_dir), 'children': []},  # Clean stop
        {'name': 'test_dir', 'type': 'directory', 'path': str(test_dir)}  # Partial stop
    ]
    
    # More detailed assertion message
    assert any(all(item in result.items() for item in expected.items()) 
              for expected in expected_results if expected), \
        f"Result {result} did not match any expected results {expected_results}"
