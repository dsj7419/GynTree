import pytest
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QApplication, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QSize, QPoint
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QFont
import logging
import gc
import psutil
from typing import Dict, List, Any
from pathlib import Path

from components.UI.ResultUI import ResultUI  # Fixed import
import time

pytestmark = pytest.mark.unit

logger = logging.getLogger(__name__)

class ResultUITestHelper:
    """Helper class for ResultUI testing"""
    def __init__(self):
        self.initial_memory = None
        self.test_data = [
            {
                'path': '/test/file1.py',
                'description': 'Test file 1 description'
            },
            {
                'path': '/test/file2.py',
                'description': 'Test file 2 description'
            }
        ]

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
            if memory_diff > 10 * 1024 * 1024:  # 10MB threshold
                logger.warning(f"High memory usage after {operation}: {memory_diff / 1024 / 1024:.2f}MB")

@pytest.fixture
def helper():
    """Create test helper instance"""
    return ResultUITestHelper()

@pytest.fixture
def mock_controller(mocker):
    """Create mock controller with required project context"""
    controller = mocker.Mock()
    project_controller = mocker.Mock()
    project_context = mocker.Mock()
    directory_analyzer = mocker.Mock()
    directory_analyzer.get_flat_structure.return_value = ResultUITestHelper().test_data
    
    project_context.directory_analyzer = directory_analyzer
    project_controller.project_context = project_context
    controller.project_controller = project_controller
    
    return controller

@pytest.fixture
def mock_theme_manager(mocker):
    """Create mock theme manager with required signal"""
    theme_manager = mocker.Mock()
    theme_manager.themeChanged = mocker.Mock()
    return theme_manager

@pytest.fixture
def mock_directory_analyzer(mocker, helper):
    """Create mock directory analyzer"""
    analyzer = mocker.Mock()
    analyzer.get_flat_structure.return_value = helper.test_data
    return analyzer

@pytest.fixture
def result_ui(qtbot, mock_controller, mock_theme_manager, mock_directory_analyzer):
    """Create ResultUI instance with proper cleanup"""
    ui = ResultUI(mock_controller, mock_theme_manager, mock_directory_analyzer)
    qtbot.addWidget(ui)
    ui.show()
    qtbot.waitForWindowShown(ui)
    
    yield ui
    
    ui.close()
    qtbot.wait(100)
    gc.collect()

@pytest.mark.timeout(30)
def test_initialization(result_ui, helper):
    """Test initial UI setup"""
    helper.track_memory()
    
    assert isinstance(result_ui, QMainWindow)
    assert result_ui.windowTitle() == 'Analysis Results'
    assert result_ui.result_table is not None
    assert result_ui.result_data is None
    
    helper.check_memory_usage("initialization")

@pytest.mark.timeout(30)
def test_ui_components(result_ui, qtbot, helper):
    """Test presence and properties of UI components"""
    helper.track_memory()
    
    # Test title
    title = result_ui.findChild(QLabel)
    assert title is not None
    assert title.text() == 'Analysis Results'
    assert title.font().pointSize() == 24
    assert title.font().weight() == QFont.Bold
    
    # Test buttons
    buttons = result_ui.findChildren(QPushButton)
    button_texts = {'Copy to Clipboard', 'Save as TXT', 'Save as CSV'}
    assert {btn.text() for btn in buttons} == button_texts
    
    helper.check_memory_usage("UI components")

@pytest.mark.timeout(30)
def test_table_setup(result_ui, helper):
    """Test table widget configuration"""
    helper.track_memory()
    
    table = result_ui.result_table
    assert table.columnCount() == 2
    assert table.horizontalHeader().sectionResizeMode(1) == QHeaderView.Stretch
    assert not table.verticalHeader().isVisible()
    assert table.wordWrap() is True
    assert table.showGrid() is True
    
    helper.check_memory_usage("table setup")

@pytest.mark.timeout(30)
def test_update_result(result_ui, qtbot, helper):
    """Test result table update"""
    helper.track_memory()
    
    with qtbot.waitSignal(result_ui.resultUpdated, timeout=1000):
        result_ui.update_result()
    
    table = result_ui.result_table
    assert table.rowCount() == len(helper.test_data)
    assert table.item(0, 0).text() == '/test/file1.py'
    assert table.item(0, 1).text() == 'Test file 1 description'
    
    helper.check_memory_usage("update result")

@pytest.mark.timeout(30)
def test_copy_to_clipboard(result_ui, qtbot, mocker, helper):
    """Test copying results to clipboard"""
    helper.track_memory()
    
    mock_clipboard = mocker.patch.object(QApplication, 'clipboard')
    result_ui.update_result()
    
    copy_btn = next(btn for btn in result_ui.findChildren(QPushButton)
                   if btn.text() == 'Copy to Clipboard')
    
    with qtbot.waitSignal(result_ui.clipboardCopyComplete, timeout=1000):
        QTest.mouseClick(copy_btn, Qt.LeftButton)
    
    mock_clipboard.return_value.setText.assert_called_once()
    clipboard_text = mock_clipboard.return_value.setText.call_args[0][0]
    assert 'Path,Description' in clipboard_text
    
    helper.check_memory_usage("clipboard copy")

@pytest.mark.timeout(30)
def test_save_csv(result_ui, qtbot, mocker, helper):
    """Test saving results as CSV"""
    helper.track_memory()
    
    # Create mock temp file object
    mock_temp_file = mocker.Mock()
    mock_temp_file.name = '/tmp/test.csv'
    mock_temp = mocker.patch('tempfile.NamedTemporaryFile', return_value=mock_temp_file)
    
    # Setup file mock
    mock_file = mocker.mock_open()
    open_mock = mocker.patch('builtins.open', mock_file)
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('shutil.copy2')
    mocker.patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName',
                return_value=('/test/output.csv', ''))
    
    result_ui.update_result()
    save_csv_btn = next(btn for btn in result_ui.findChildren(QPushButton)
                       if btn.text() == 'Save as CSV')
    
    with qtbot.waitSignal(result_ui.saveComplete, timeout=1000):
        QTest.mouseClick(save_csv_btn, Qt.LeftButton)
    
    # Verify temp file was created and written to
    mock_temp.assert_called_once()
    calls = open_mock.mock_calls
    assert len(calls) > 0
    
    helper.check_memory_usage("save CSV")

@pytest.mark.timeout(30)
def test_error_handling(result_ui, qtbot, mocker, helper):
    """Test error handling in save operations"""
    helper.track_memory()
    
    # Mock file operations to raise exception
    mocker.patch('builtins.open', side_effect=Exception("Test error"))
    mocker.patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName',
                return_value=('/test/output.txt', ''))
    
    result_ui.update_result()
    save_txt_btn = next(btn for btn in result_ui.findChildren(QPushButton)
                       if btn.text() == 'Save as TXT')
    
    with qtbot.waitSignal(result_ui.error, timeout=1000):
        QTest.mouseClick(save_txt_btn, Qt.LeftButton)
    
    helper.check_memory_usage("error handling")

@pytest.mark.timeout(30)
def test_large_dataset(result_ui, qtbot, mock_directory_analyzer, helper):
    """Test handling of large datasets"""
    helper.track_memory()
    
    # Create large dataset
    large_data = [
        {
            'path': f'/test/file{i}.py',
            'description': f'Test file {i} description' * 10
        }
        for i in range(1000)
    ]
    mock_directory_analyzer.get_flat_structure.return_value = large_data
    
    start_time = time.time()
    with qtbot.waitSignal(result_ui.resultUpdated, timeout=5000):
        result_ui.update_result()
    duration = time.time() - start_time
    
    assert duration < 2.0  # Should complete within 2 seconds
    assert result_ui.result_table.rowCount() == 1000
    
    helper.check_memory_usage("large dataset")

@pytest.mark.timeout(30)
def test_window_resize(result_ui, qtbot, helper):
    """Test window resize handling"""
    helper.track_memory()
    
    original_size = result_ui.size()
    result_ui.resize(original_size.width() + 100, original_size.height() + 100)
    qtbot.wait(100)
    
    # Verify column widths adjusted
    assert result_ui.result_table.columnWidth(0) > 0
    assert result_ui.result_table.columnWidth(1) > 0
    total_width = (result_ui.result_table.columnWidth(0) + 
                  result_ui.result_table.columnWidth(1))
    assert total_width <= result_ui.result_table.viewport().width()
    
    helper.check_memory_usage("window resize")

@pytest.mark.timeout(30)
def test_rapid_updates(result_ui, qtbot, helper):
    """Test UI stability during rapid updates"""
    helper.track_memory()
    
    # Perform rapid updates
    for _ in range(10):
        result_ui.update_result()
        qtbot.wait(10)  # Minimal wait to simulate rapid updates
    
    assert result_ui.result_table.rowCount() > 0
    assert result_ui.result_table.isVisible()
    
    helper.check_memory_usage("rapid updates")

@pytest.mark.timeout(30)
def test_sort_functionality(result_ui, qtbot, helper):
    """Test table sorting functionality"""
    helper.track_memory()
    
    result_ui.update_result()
    
    # Click header to sort
    header = result_ui.result_table.horizontalHeader()
    header_pos = header.sectionPosition(0) + header.sectionSize(0) // 2
    QTest.mouseClick(header.viewport(), Qt.LeftButton, pos=QPoint(header_pos, 5))
    qtbot.wait(100)
    
    # Verify sorting
    first_item = result_ui.result_table.item(0, 0).text()
    last_item = result_ui.result_table.item(result_ui.result_table.rowCount() - 1, 0).text()
    assert first_item <= last_item
    
    helper.check_memory_usage("sort functionality")

@pytest.mark.timeout(30)
def test_theme_application(result_ui, helper):
    """Test theme application to UI"""
    helper.track_memory()
    
    result_ui.apply_theme()
    result_ui.theme_manager.apply_theme.assert_called_with(result_ui)
    
    helper.check_memory_usage("theme application")

@pytest.mark.timeout(30)
def test_memory_cleanup(result_ui, qtbot, helper):
    """Test memory cleanup during UI operations"""
    helper.track_memory()
    
    # Perform memory-intensive operations
    for _ in range(10):
        result_ui.update_result()
        qtbot.wait(50)
        gc.collect()
    
    # Clear table
    result_ui.result_table.clear()
    result_ui.result_data = None
    gc.collect()
    
    final_memory = psutil.Process().memory_info().rss
    memory_diff = final_memory - helper.initial_memory
    assert memory_diff < 10 * 1024 * 1024  # Less than 10MB increase
    
    helper.check_memory_usage("memory cleanup")

@pytest.mark.timeout(30)
def test_concurrent_operations(result_ui, qtbot, mocker, helper):
    """Test handling of concurrent operations"""
    helper.track_memory()
    
    # Mock file operations
    mock_file = mocker.mock_open()
    mocker.patch('builtins.open', mock_file)
    mocker.patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName',
                return_value=('/test/output.txt', ''))
    
    # Simulate concurrent operations
    result_ui.update_result()
    
    # Wait for update completion
    qtbot.wait(100)
    
    save_txt_btn = next(btn for btn in result_ui.findChildren(QPushButton)
                       if btn.text() == 'Save as TXT')
    
    with qtbot.waitSignal(result_ui.saveComplete, timeout=1000):
        QTest.mouseClick(save_txt_btn, Qt.LeftButton)
    
    copy_btn = next(btn for btn in result_ui.findChildren(QPushButton)
                   if btn.text() == 'Copy to Clipboard')
    
    with qtbot.waitSignal(result_ui.clipboardCopyComplete, timeout=1000):
        QTest.mouseClick(copy_btn, Qt.LeftButton)
    
    helper.check_memory_usage("concurrent operations")

@pytest.mark.timeout(30)
def test_ui_responsiveness(result_ui, qtbot, helper):
    """Test UI responsiveness during operations"""
    helper.track_memory()
    
    start_time = time.time()
    
    # Perform multiple UI operations
    for _ in range(5):
        result_ui.update_result()
        qtbot.wait(10)
        result_ui.copy_to_clipboard()
        qtbot.wait(10)
    
    duration = time.time() - start_time
    assert duration < 2.0  # Should complete within 2 seconds
    
    helper.check_memory_usage("UI responsiveness")

@pytest.mark.timeout(30)
def test_table_selection(result_ui, qtbot, helper):
    """Test table selection handling"""
    helper.track_memory()
    
    result_ui.update_result()
    
    # Select some items
    result_ui.result_table.setSelectionMode(QTableWidget.MultiSelection)
    result_ui.result_table.selectRow(0)
    qtbot.wait(100)
    
    selected_items = result_ui.result_table.selectedItems()
    assert len(selected_items) > 0
    
    helper.check_memory_usage("table selection")

@pytest.mark.timeout(30)
def test_column_resize(result_ui, qtbot, helper):
    """Test column resize handling"""
    helper.track_memory()
    
    result_ui.update_result()
    
    # Resize columns
    result_ui.result_table.setColumnWidth(0, 200)
    qtbot.wait(100)
    
    assert result_ui.result_table.columnWidth(0) == 200
    assert result_ui.result_table.columnWidth(1) > 0
    
    helper.check_memory_usage("column resize")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])