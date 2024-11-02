import pytest
import psutil
import gc
import time
import math
import os
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.SettingsManager import SettingsManager
from models.Project import Project

pytestmark = [pytest.mark.performance, pytest.mark.slow]

@pytest.fixture
def create_large_directory_structure(tmp_path):
    """Create a test directory structure with controlled size."""
    def _create_large_directory_structure(depth=3, files_per_dir=50):
        def create_files(directory, num_files):
            for i in range(num_files):
                file_path = directory / f"file_{i}.txt"
                file_path.write_text(f"# GynTree: Test file {i}")

        def create_dirs(root, current_depth, prefix=''):
            if current_depth > depth:
                return
            create_files(root, files_per_dir)
            for i in range(3):  # Limit to 3 subdirs for controlled growth
                subdir = root / f"{prefix}dir_{i}"
                subdir.mkdir(exist_ok=True)
                create_dirs(subdir, current_depth + 1, f"{prefix}{i}_")

        # Create a unique test directory for each test run
        test_dir = tmp_path / f"test_dir_{time.time_ns()}"
        test_dir.mkdir(exist_ok=True)
        create_dirs(test_dir, 1)
        return test_dir
    return _create_large_directory_structure

@pytest.fixture
def mock_project(tmp_path):
    return Project(
        name="test_project",
        start_directory=str(tmp_path),
        root_exclusions=[],
        excluded_dirs=[],
        excluded_files=[]
    )

@pytest.fixture
def settings_manager(mock_project):
    return SettingsManager(mock_project)

@pytest.fixture
def analyzer_setup(tmp_path, settings_manager):
    """Setup and teardown for analyzer tests."""
    process = psutil.Process()
    gc.collect()
    initial_memory = process.memory_info().rss
    
    yield DirectoryAnalyzer(str(tmp_path), settings_manager)
    
    gc.collect()
    final_memory = process.memory_info().rss
    memory_diff = final_memory - initial_memory
    print(f"\nMemory difference: {memory_diff / 1024 / 1024:.2f}MB")

@pytest.mark.timeout(60)
def test_directory_analyzer_memory_usage(create_large_directory_structure, settings_manager):
    """Test memory usage during directory analysis."""
    large_dir = create_large_directory_structure(depth=3, files_per_dir=50)
    analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
    
    process = psutil.Process()
    gc.collect()
    memory_before = process.memory_info().rss
    
    result = analyzer.analyze_directory()
    
    gc.collect()
    memory_after = process.memory_info().rss
    memory_increase = memory_after - memory_before
    
    max_allowed_increase = 50 * 1024 * 1024  # 50MB
    assert memory_increase < max_allowed_increase, \
        f"Memory usage increased by {memory_increase / (1024 * 1024):.2f}MB"
    assert len(result['children']) > 0

@pytest.mark.timeout(60)
def test_directory_analyzer_performance(create_large_directory_structure, settings_manager):
    """Test analysis performance with large directory structure."""
    large_dir = create_large_directory_structure(depth=3, files_per_dir=50)
    analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
    
    start_time = time.time()
    result = analyzer.analyze_directory()
    execution_time = time.time() - start_time
    
    assert execution_time < 15, \
        f"Analysis took {execution_time:.2f} seconds"
    assert len(result['children']) > 0

@pytest.mark.timeout(120)
def test_directory_analyzer_scalability(create_large_directory_structure, settings_manager):
    """Test analysis scalability with increasing directory sizes."""
    depths = [2, 3]
    execution_times = []
    
    for depth in depths:
        large_dir = create_large_directory_structure(depth=depth, files_per_dir=25)
        analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
        
        start_time = time.time()
        result = analyzer.analyze_directory()
        execution_time = time.time() - start_time
        execution_times.append(execution_time)
        
        print(f"Depth {depth}: Analysis completed in {execution_time:.2f} seconds")
    
    if len(execution_times) > 1:
        scaling_factor = execution_times[-1] / execution_times[0]
        expected_factor = 3  # Approximate expected growth
        assert scaling_factor < expected_factor * 1.5, \
            f"Performance scaling higher than expected: {scaling_factor:.2f}x"

@pytest.mark.timeout(60)
def test_directory_analyzer_with_exclusions(create_large_directory_structure, settings_manager):
    """Test analyzer performance with exclusions."""
    large_dir = create_large_directory_structure(depth=3, files_per_dir=25)
    
    settings_manager.add_excluded_dir("dir_0")
    settings_manager.add_excluded_file("file_0.txt")
    
    analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
    
    start_time = time.time()
    result = analyzer.analyze_directory()
    execution_time = time.time() - start_time
    
    assert execution_time < 10, \
        f"Analysis with exclusions took {execution_time:.2f} seconds"
    assert not any(child['name'] == "dir_0" for child in result['children'])
    assert not any(child['name'] == "file_0.txt" for child in result['children'])

@pytest.mark.timeout(120)
def test_directory_analyzer_memory_leak(create_large_directory_structure, settings_manager):
    """Test for memory leaks during repeated analysis."""
    large_dir = create_large_directory_structure(depth=2, files_per_dir=25)
    analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
    
    process = psutil.Process()
    initial_memory = None
    
    for i in range(3):
        gc.collect()
        if initial_memory is None:
            initial_memory = process.memory_info().rss
            
        result = analyzer.analyze_directory()
        
        gc.collect()
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory
        
        print(f"Iteration {i+1}: Memory delta {memory_increase / (1024 * 1024):.2f}MB")
        
        if i > 0:
            assert memory_increase < 20 * 1024 * 1024, \
                f"Potential memory leak detected: {memory_increase / (1024 * 1024):.2f}MB increase"