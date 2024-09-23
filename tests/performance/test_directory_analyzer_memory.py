import pytest
import psutil
import gc
import time
import math
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.SettingsManager import SettingsManager
from models.Project import Project

pytestmark = [pytest.mark.performance, pytest.mark.slow]

@pytest.fixture
def create_large_directory_structure(tmpdir):
    def _create_large_directory_structure(depth=5, files_per_dir=100):
        def create_files(directory, num_files):
            for i in range(num_files):
                file_path = directory.join(f"file_{i}.txt")
                file_path.write(f"# GynTree: Test file {i}")

        def create_dirs(root, current_depth):
            if current_depth > depth:
                return
            create_files(root, files_per_dir)
            for i in range(5):
                subdir = root.mkdir(f"dir_{i}")
                create_dirs(subdir, current_depth + 1)

        create_dirs(tmpdir, 1)
        return tmpdir

    return _create_large_directory_structure

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

def test_directory_analyzer_memory_usage(create_large_directory_structure, settings_manager):
    large_dir = create_large_directory_structure(depth=5, files_per_dir=100)
    
    mock_project = Project(name="test_project", start_directory=str(large_dir))
    analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
    
    process = psutil.Process()
    
    gc.collect()
    memory_before = process.memory_info().rss
    
    result = analyzer.analyze_directory()
    
    gc.collect()
    memory_after = process.memory_info().rss
    
    memory_increase = memory_after - memory_before
    
    # Assert memory increase is within acceptable limits (e.g., less than 100 MB)
    max_allowed_increase = 100 * 1024 * 1024  # 100 MB in bytes
    assert memory_increase < max_allowed_increase, f"Memory usage increased by {memory_increase / (1024 * 1024):.2f} MB, which exceeds the limit of {max_allowed_increase / (1024 * 1024)} MB"
    
    assert len(result['children']) > 0, "The analysis did not produce any results"
    
    print(f"Memory usage increased by {memory_increase / (1024 * 1024):.2f} MB")

def test_directory_analyzer_performance(create_large_directory_structure, settings_manager):
    large_dir = create_large_directory_structure(depth=5, files_per_dir=100)
    
    mock_project = Project(name="test_project", start_directory=str(large_dir))
    analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
    
    start_time = time.time()
    
    result = analyzer.analyze_directory()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    assert execution_time < 30, f"Analysis took {execution_time:.2f} seconds, which exceeds the 30 second limit"
    
    assert len(result['children']) > 0, "The analysis did not produce any results"
    
    print(f"Analysis completed in {execution_time:.2f} seconds")

def test_directory_analyzer_scalability(create_large_directory_structure, settings_manager):
    depths = [3, 4, 5]
    execution_times = []
    
    for depth in depths:
        large_dir = create_large_directory_structure(depth=depth, files_per_dir=50)
        mock_project = Project(name="test_project", start_directory=str(large_dir))
        analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
        
        start_time = time.time()
        
        result = analyzer.analyze_directory()
        
        end_time = time.time()
        execution_time = end_time - start_time
        execution_times.append(execution_time)
        
        print(f"Depth {depth}: Analysis completed in {execution_time:.2f} seconds")
    
    time_ratios = [execution_times[i+1] / execution_times[i] for i in range(len(execution_times)-1)]
    average_ratio = sum(time_ratios) / len(time_ratios)
    
    assert 4 < average_ratio < 6, f"Average time ratio {average_ratio:.2f} is not close to the expected value of 5"

def test_directory_analyzer_with_exclusions(create_large_directory_structure, settings_manager):
    large_dir = create_large_directory_structure(depth=5, files_per_dir=100)
    
    settings_manager.add_excluded_dir("dir_0")
    settings_manager.add_excluded_file("file_0.txt")
    
    mock_project = Project(name="test_project", start_directory=str(large_dir))
    analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
    
    start_time = time.time()
    
    result = analyzer.analyze_directory()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    assert not any(child['name'] == "dir_0" for child in result['children']), "Excluded directory found in results"
    assert not any(child['name'] == "file_0.txt" for child in result['children']), "Excluded file found in results"
    
    print(f"Analysis with exclusions completed in {execution_time:.2f} seconds")

def test_directory_analyzer_memory_leak(create_large_directory_structure, settings_manager):
    large_dir = create_large_directory_structure(depth=4, files_per_dir=50)
    mock_project = Project(name="test_project", start_directory=str(large_dir))
    analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
    
    process = psutil.Process()
    
    for i in range(5):
        gc.collect()
        memory_before = process.memory_info().rss
        
        result = analyzer.analyze_directory()
        
        gc.collect()
        memory_after = process.memory_info().rss
        
        memory_increase = memory_after - memory_before
        print(f"Iteration {i+1}: Memory usage increased by {memory_increase / (1024 * 1024):.2f} MB")
        
        if i > 0:
            assert memory_increase < 10 * 1024 * 1024, f"Potential memory leak detected. Memory increased by {memory_increase / (1024 * 1024):.2f} MB in iteration {i+1}"

def test_directory_analyzer_cpu_usage(create_large_directory_structure, settings_manager):
    large_dir = create_large_directory_structure(depth=5, files_per_dir=100)
    mock_project = Project(name="test_project", start_directory=str(large_dir))
    analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
    
    process = psutil.Process()
    
    start_time = time.time()
    start_cpu_time = process.cpu_times().user + process.cpu_times().system
    
    result = analyzer.analyze_directory()
    
    end_time = time.time()
    end_cpu_time = process.cpu_times().user + process.cpu_times().system
    
    wall_time = end_time - start_time
    cpu_time = end_cpu_time - start_cpu_time
    
    cpu_usage = cpu_time / wall_time
    
    print(f"CPU usage: {cpu_usage:.2f} (ratio of CPU time to wall time)")
    
    # Check that CPU usage is reasonable (e.g., not using more than 2 cores on average)
    assert cpu_usage < 2, f"CPU usage ({cpu_usage:.2f}) is higher than expected"

def test_directory_analyzer_with_very_deep_structure(create_large_directory_structure, settings_manager):
    very_deep_dir = create_large_directory_structure(depth=10, files_per_dir=10)
    mock_project = Project(name="test_project", start_directory=str(very_deep_dir))
    analyzer = DirectoryAnalyzer(str(very_deep_dir), settings_manager)
    
    start_time = time.time()
    
    result = analyzer.analyze_directory()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"Analysis of very deep structure completed in {execution_time:.2f} seconds")
    
    max_depth = 0
    def get_max_depth(node, current_depth):
        nonlocal max_depth
        max_depth = max(max_depth, current_depth)
        for child in node.get('children', []):
            if child['type'] == 'directory':
                get_max_depth(child, current_depth + 1)
    
    get_max_depth(result, 0)
    assert max_depth >= 10, f"Analysis did not capture the full depth of the directory structure. Max depth: {max_depth}"

def test_directory_analyzer_with_large_files(create_large_directory_structure, settings_manager, tmpdir):
    large_dir = create_large_directory_structure(depth=3, files_per_dir=10)
    
    for i in range(5):
        large_file = large_dir.join(f"large_file_{i}.txt")
        with large_file.open('w') as f:
            f.write('0' * (10 * 1024 * 1024))  # 10 MB file
    
    mock_project = Project(name="test_project", start_directory=str(large_dir))
    analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)
    
    start_time = time.time()
    
    result = analyzer.analyze_directory()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"Analysis with large files completed in {execution_time:.2f} seconds")
    
    large_files = [child for child in result['children'] if child['name'].startswith('large_file_')]
    assert len(large_files) == 5, f"Expected 5 large files, but found {len(large_files)}"