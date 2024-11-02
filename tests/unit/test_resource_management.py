import gc
import pytest
import os 
import psutil
import time
from unittest.mock import Mock, patch, MagicMock, create_autospec
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import QTimer, Qt
import tempfile

from components.TreeExporter import TreeExporter
from services.DirectoryAnalyzer import DirectoryAnalyzer
from controllers.ThreadController import ThreadController
from services.ProjectContext import ProjectContext
from models.Project import Project

# Import conftest utilities
from conftest import (
    test_artifacts
)

def get_process_memory():
    """Helper function to get current process memory usage"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

@pytest.fixture
def app():
    return QApplication([])

@pytest.fixture
def tree_widget():
    widget = QTreeWidget()
    widget.setColumnCount(2)
    widget.setHeaderLabels(['Name', 'Type'])
    return widget

@pytest.fixture
def mock_project():
    # Create a proper Project mock that mimics all required attributes
    project = create_autospec(Project, instance=True)
    project.name = "test"
    project.start_directory = "/test/path"
    project.root_exclusions = []
    project.excluded_dirs = []  # Add this missing attribute
    return project

class TestResourceManagement:
    def test_tree_exporter_temp_file_cleanup(self, tree_widget):
        exporter = TreeExporter(tree_widget)
        temp_files = [
            tempfile.mktemp(suffix='.png'),
            tempfile.mktemp(suffix='.txt')
        ]
        
        # Simulate temp file creation
        for temp_file in temp_files:
            with open(temp_file, 'w') as f:
                f.write('test')
            exporter._temp_files.append(temp_file)
        
        # Verify cleanup
        exporter._cleanup_temp_files()
        for temp_file in temp_files:
            assert not os.path.exists(temp_file)
        assert len(exporter._temp_files) == 0

    @pytest.mark.timeout(10)
    def test_directory_analyzer_memory_stability(self):
        settings_manager = Mock()
        settings_manager.excluded_dirs = []
        analyzer = DirectoryAnalyzer('/test/path', settings_manager)
        
        initial_memory = get_process_memory()
        
        # Mock analyze_directory to prevent actual file system access
        with patch.object(analyzer.directory_structure_service, 'get_hierarchical_structure', 
                         return_value={'children': []}):
            # Perform multiple analysis operations
            for _ in range(5):
                analyzer.analyze_directory()
        
            # Allow time for garbage collection
            time.sleep(0.1)
            
            final_memory = get_process_memory()
            memory_increase = final_memory - initial_memory
            
            # Check memory increase is reasonable (less than 100MB)
            assert memory_increase < 100_000_000, \
                f"Memory increase ({memory_increase} bytes) exceeds threshold"

    def test_thread_controller_resource_cleanup(self):
        controller = ThreadController()
        
        # Create some mock workers
        mock_workers = [Mock() for _ in range(3)]
        for worker in mock_workers:
            worker.signals = Mock()
            worker.signals.cleanup = Mock()
            controller.active_workers.append(worker)
        
        # Test cleanup
        controller.cleanup_thread()
        
        # Verify all workers received cleanup signal
        for worker in mock_workers:
            assert worker.signals.cleanup.emit.called
        
        # Verify workers list is cleared
        assert len(controller.active_workers) == 0

    def test_project_context_resource_lifecycle(self, mock_project):
        context = ProjectContext(mock_project)
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('services.SettingsManager.SettingsManager.load_settings', 
                   return_value={'excluded_dirs': [], 'root_exclusions': []}):
            with patch.object(context, 'initialize_directory_analyzer'), \
                 patch.object(context, 'initialize_auto_exclude_manager'), \
                 patch.object(context, 'detect_project_types'):
                context.initialize()
        
        # Test cleanup
        context.close()
        assert context.directory_analyzer is None
        assert context.auto_exclude_manager is None
        assert not context._is_active

    def test_tree_exporter_large_file_handling(self, tree_widget):
        exporter = TreeExporter(tree_widget)
        
        # Create a large temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'x' * 1024 * 1024)  # 1MB file
            temp_path = tmp.name
        
        try:
            with patch('PyQt5.QtGui.QPixmap.save', return_value=True), \
                 patch('PyQt5.QtWidgets.QTreeWidget.render'):  # Mock render to prevent GUI operations
                success = exporter._render_and_save_pixmap(tree_widget, 800, 600, temp_path)
                assert success
        finally:
            os.unlink(temp_path)

    def test_analyzer_stop_event_cleanup(self):
        analyzer = DirectoryAnalyzer('/test/path', Mock())
        
        # Simulate analysis with stop
        analyzer.stop()
        result = analyzer.analyze_directory()
        
        assert analyzer._stop_event.is_set()
        assert isinstance(result, dict)

    def test_ui_component_cleanup(self, qapp):
        """Test UI component resource cleanup with enhanced safety measures"""
        widget = None
        timer = None
        
        try:
            widget = QTreeWidget()
            test_artifacts.track_widget(widget)  # Track widget for cleanup
            
            widget.setColumnCount(2)
            widget.setHeaderLabels(['Name', 'Type'])
            
            # Add items with timer to process events
            timer = QTimer()
            timer.setInterval(10)  # 10ms between batches
            items_to_add = []
            
            # Prepare items first
            for i in range(5):  # Reduced to 5 items for stability
                item = QTreeWidgetItem()
                item.setText(0, f"Item {i}")
                item.setText(1, "Type")
                items_to_add.append(item)
            
            # Add items and process events
            QApplication.processEvents()
            widget.addTopLevelItems(items_to_add)
            QApplication.processEvents()
            
            # Extra event processing
            for _ in range(3):
                QApplication.processEvents()
            
            # Verify items were added
            count = widget.topLevelItemCount()
            assert count == 5, f"Expected 5 items, got {count}"
            
            # Clear items with careful event processing
            items_to_add.clear()
            widget.clear()
            QApplication.processEvents()
            
            # Process events again
            for _ in range(3):
                QApplication.processEvents()
            
            # Final verification
            assert widget.topLevelItemCount() == 0
            
        finally:
            if timer:
                timer.stop()
                timer.deleteLater()
            
            if widget:
                widget.clear()
                QApplication.processEvents()
                widget.setParent(None)
                widget.deleteLater()
                QApplication.processEvents()
                
                # Use test artifacts cleanup
                test_artifacts._cleanup_qt_widgets()
                
            # Final event processing and garbage collection
            for _ in range(3):
                QApplication.processEvents()
                time.sleep(0.01)
            gc.collect()

    def test_project_context_memory_cleanup(self, mock_project):
        initial_memory = get_process_memory()
        
        # Create and cleanup multiple contexts
        for _ in range(5):
            context = ProjectContext(mock_project)
            
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('services.SettingsManager.SettingsManager.load_settings',
                       return_value={'excluded_dirs': [], 'root_exclusions': []}):
                try:
                    context.close()
                except:
                    pass
            
            QApplication.processEvents()  # Allow event processing
        
        # Allow time for garbage collection
        time.sleep(0.1)
        
        final_memory = get_process_memory()
        memory_increase = final_memory - initial_memory
        
        # Check memory increase is reasonable (less than 50MB)
        assert memory_increase < 50_000_000, \
            f"Memory increase ({memory_increase} bytes) exceeds threshold"