import pytest
import psutil
import gc
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.SettingsManager import SettingsManager
from models.Project import Project

@pytest.mark.memory
def test_directory_analyzer_memory_usage(create_large_directory_structure, settings_manager):

    large_dir = create_large_directory_structure(depth=5, files_per_dir=100)

    # Set up the DirectoryAnalyzer
    mock_project = Project(name="test_project", start_directory=str(large_dir))
    analyzer = DirectoryAnalyzer(str(large_dir), settings_manager)

    # Get the current process
    process = psutil.Process()

    # Measure memory usage before analysis
    gc.collect()
    memory_before = process.memory_info().rss

    # Perform the analysis
    result = analyzer.analyze_directory()

    # Measure memory usage after analysis
    gc.collect()
    memory_after = process.memory_info().rss

    # Calculate memory increase
    memory_increase = memory_after - memory_before

    # Assert that memory increase is within acceptable limits (e.g., less than 100 MB)
    max_allowed_increase = 100 * 1024 * 1024  # 100 MB in bytes
    assert memory_increase < max_allowed_increase, f"Memory usage increased by {memory_increase / (1024 * 1024):.2f} MB, which exceeds the limit of {max_allowed_increase / (1024 * 1024)} MB"

    # Check that the analysis completed successfully
    assert len(result) > 0, "The analysis did not produce any results"

    # Optional: Print memory usage for informational purposes
    print(f"Memory usage increased by {memory_increase / (1024 * 1024):.2f} MB")