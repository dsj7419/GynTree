import pytest
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QPushButton, QTreeWidget
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
import os
import time
import gc
import psutil
from components.UI.ExclusionsManagerUI import ExclusionsManagerUI

class _TestData:
    """Class to maintain state for testing"""
    def __init__(self):
        self.data = {
            'root_exclusions': set(),
            'excluded_dirs': set(),
            'excluded_files': set()
        }

    def update(self, new_data):
        """Update test data"""
        if not isinstance(new_data, dict):
            return
        for key, value in new_data.items():
            if key in self.data:
                self.data[key] = set(value) if isinstance(value, (list, set)) else set()

    def get(self, key, default=None):
        """Get data with default value"""
        return set(self.data.get(key, default or set()))

    def get_all(self):
        """Get copy of all data"""
        return {k: set(v) for k, v in self.data.items()}

@pytest.fixture
def mock_settings_manager(mocker):
    """Create a properly configured settings manager mock"""
    mock = mocker.Mock()
    test_data = _TestData()  # Use the renamed class
    
    # Setup core functionality
    mock.get_all_exclusions = mocker.Mock(side_effect=test_data.get_all)
    mock.get_root_exclusions = mocker.Mock(side_effect=lambda: test_data.get('root_exclusions'))
    mock.update_settings = mocker.Mock(side_effect=test_data.update)
    mock.save_settings = mocker.Mock(return_value=True)
    
    return mock

@pytest.fixture
def mock_theme_manager(mocker):
    mock = mocker.Mock()
    mock.themeChanged = mocker.Mock()
    mock.apply_theme = mocker.Mock()
    return mock

@pytest.fixture
def mock_controller(mocker):
    controller = mocker.Mock()
    project_controller = mocker.Mock()
    project_context = mocker.Mock()
    project = mocker.Mock()
    
    project.start_directory = "/test/project"
    project_context.project = project
    project_context.is_initialized = True
    project_controller.project_context = project_context
    controller.project_controller = project_controller
    
    return controller

@pytest.fixture
def mock_dialogs(mocker):
    """Mock all dialog interactions"""
    mocker.patch.object(QMessageBox, 'information', return_value=QMessageBox.Ok)
    mocker.patch.object(QMessageBox, 'warning', return_value=QMessageBox.Ok)
    mocker.patch.object(QFileDialog, 'getExistingDirectory', return_value="/test/project/subfolder")
    mocker.patch.object(QFileDialog, 'getOpenFileName', return_value=("/test/project/test.txt", ""))
    return mocker

@pytest.fixture
def exclusions_ui(qtbot, mock_controller, mock_settings_manager, mock_theme_manager, mock_dialogs):
    """Create the ExclusionsManagerUI instance with proper mocks"""
    ui = ExclusionsManagerUI(mock_controller, mock_theme_manager, mock_settings_manager)  # Use mock directly
    ui._skip_show_event = True  # Skip the show event for testing
    qtbot.addWidget(ui)
    return ui

def test_initialization(exclusions_ui):
    """Test basic initialization"""
    assert exclusions_ui.windowTitle() == 'Exclusions Manager'
    assert exclusions_ui.exclusion_tree is not None
    assert exclusions_ui.root_tree is not None

def test_tree_widgets_setup(exclusions_ui):
    """Test tree widget initialization"""
    assert exclusions_ui.exclusion_tree.headerItem().text(0) == 'Type'
    assert exclusions_ui.exclusion_tree.headerItem().text(1) == 'Path'

def test_add_directory(exclusions_ui, qtbot):
    """Test adding a directory"""
    initial_count = len(exclusions_ui.settings_manager.get_all_exclusions()['excluded_dirs'])
    
    add_dir_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                      if btn.text() == 'Add Directory')
    
    qtbot.mouseClick(add_dir_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    current_exclusions = exclusions_ui.settings_manager.get_all_exclusions()
    assert len(current_exclusions['excluded_dirs']) == initial_count + 1

def test_add_file(exclusions_ui, qtbot):
    """Test adding a file"""
    initial_count = len(exclusions_ui.settings_manager.get_all_exclusions()['excluded_files'])
    
    add_file_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                       if btn.text() == 'Add File')
    
    qtbot.mouseClick(add_file_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    current_exclusions = exclusions_ui.settings_manager.get_all_exclusions()
    assert len(current_exclusions['excluded_files']) == initial_count + 1

def test_remove_selected(exclusions_ui, qtbot):
    """Test removing selected items"""
    # Setup test data
    test_data = {
        'excluded_dirs': {'test_dir'},
        'excluded_files': set(),
        'root_exclusions': set()
    }
    exclusions_ui.settings_manager.update_settings(test_data)
    
    # Populate and select item
    exclusions_ui.populate_exclusion_tree()
    qtbot.wait(100)
    
    dirs_item = exclusions_ui.exclusion_tree.topLevelItem(0)
    test_item = dirs_item.child(0)
    exclusions_ui.exclusion_tree.setCurrentItem(test_item)
    
    # Remove the item
    remove_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                    if btn.text() == 'Remove Selected')
    qtbot.mouseClick(remove_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    # Verify
    current_data = exclusions_ui.settings_manager.get_all_exclusions()
    assert 'test_dir' not in current_data['excluded_dirs']

def test_populate_trees(exclusions_ui, qtbot):
    """Test populating tree widgets"""
    test_data = {
        'root_exclusions': {'root1', 'root2'},
        'excluded_dirs': {'dir1', 'dir2'},
        'excluded_files': {'file1.txt', 'file2.txt'}
    }
    
    # Update settings
    exclusions_ui.settings_manager.update_settings(test_data)
    
    # Populate trees
    exclusions_ui.populate_exclusion_tree()
    exclusions_ui.populate_root_exclusions()
    qtbot.wait(100)
    
    # Verify structure
    assert exclusions_ui.exclusion_tree.topLevelItemCount() == 2
    dirs_item = exclusions_ui.exclusion_tree.topLevelItem(0)
    files_item = exclusions_ui.exclusion_tree.topLevelItem(1)
    
    assert dirs_item.text(0) == 'Excluded Dirs'
    assert files_item.text(0) == 'Excluded Files'
    assert dirs_item.childCount() == 2
    assert files_item.childCount() == 2

def test_save_and_exit(exclusions_ui, qtbot, mocker):
    """Test save and exit functionality"""
    # Mock to prevent actual window closing
    close_mock = mocker.patch.object(exclusions_ui, 'close')
    
    # Setup test data
    test_data = {
        'root_exclusions': {'root1'},
        'excluded_dirs': {'dir1'},
        'excluded_files': {'file1.txt'}
    }
    exclusions_ui.settings_manager.get_all_exclusions.return_value = {
        k: set(v) for k, v in test_data.items()
    }
    
    # Populate the trees
    exclusions_ui.populate_exclusion_tree()
    exclusions_ui.populate_root_exclusions()
    qtbot.wait(100)
    
    # Click save button
    save_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                   if btn.text() == 'Save & Exit')
    qtbot.mouseClick(save_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    # Verify saves were called
    exclusions_ui.settings_manager.update_settings.assert_called()
    exclusions_ui.settings_manager.save_settings.assert_called_once()
    close_mock.assert_called_once()

def test_theme_application(exclusions_ui):
    """Test theme application"""
    exclusions_ui.theme_manager.apply_theme.reset_mock()
    exclusions_ui.apply_theme()
    exclusions_ui.theme_manager.apply_theme.assert_called_once_with(exclusions_ui)

def test_large_exclusion_list(exclusions_ui, qtbot):
    """Test handling of large exclusion lists"""
    large_data = {
        'root_exclusions': {f'root_{i}' for i in range(1000)},
        'excluded_dirs': {f'dir_{i}' for i in range(1000)},
        'excluded_files': {f'file_{i}.txt' for i in range(1000)}
    }
    
    def mock_get_exclusions():
        return {k: set(v) for k, v in large_data.items()}
    exclusions_ui.settings_manager.get_all_exclusions.side_effect = mock_get_exclusions
    
    start_time = time.time()
    exclusions_ui.populate_exclusion_tree()
    qtbot.wait(500)
    end_time = time.time()
    
    assert (end_time - start_time) < 5.0
    assert exclusions_ui.exclusion_tree.topLevelItemCount() == 2
    dirs_item = exclusions_ui.exclusion_tree.topLevelItem(0)
    assert dirs_item.childCount() == 1000

def test_memory_management(exclusions_ui, qtbot):
    """Test memory management during operations"""
    test_data = {
        'root_exclusions': {f'root_{i}' for i in range(100)},
        'excluded_dirs': {f'dir_{i}' for i in range(100)},
        'excluded_files': {f'file_{i}.txt' for i in range(100)}
    }
    
    def mock_get_exclusions():
        return {k: set(v) for k, v in test_data.items()}
    exclusions_ui.settings_manager.get_all_exclusions.side_effect = mock_get_exclusions
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    exclusions_ui.populate_exclusion_tree()
    qtbot.wait(200)
    gc.collect()
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    assert memory_increase < 10 * 1024 * 1024

def test_no_project_handling(exclusions_ui, qtbot):
    """Test handling when no project is loaded"""
    exclusions_ui.settings_manager = None
    
    add_dir_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                      if btn.text() == 'Add Directory')
    
    qtbot.mouseClick(add_dir_btn, Qt.LeftButton)
    qtbot.wait(100)

def test_duplicate_entries(exclusions_ui, qtbot):
    """Test handling of duplicate entries"""
    # Setup existing exclusion
    test_data = {
        'root_exclusions': set(),
        'excluded_dirs': {'subfolder'},
        'excluded_files': set()
    }
    exclusions_ui.settings_manager.update_settings(test_data)
    
    add_dir_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                      if btn.text() == 'Add Directory')
    
    qtbot.mouseClick(add_dir_btn, Qt.LeftButton)
    qtbot.wait(100)

def test_relative_path_handling(exclusions_ui, qtbot):
    """Test handling of relative paths"""
    project_dir = "/test/project"
    absolute_path = "/test/project/subfolder"
    relative_path = os.path.relpath(absolute_path, project_dir)
    
    test_data = {
        'root_exclusions': set(),
        'excluded_dirs': {relative_path},
        'excluded_files': set()
    }
    
    def mock_get_exclusions():
        return {k: set(v) for k, v in test_data.items()}
    exclusions_ui.settings_manager.get_all_exclusions.side_effect = mock_get_exclusions
    
    exclusions_ui.populate_exclusion_tree()
    qtbot.wait(100)
    
    dirs_item = exclusions_ui.exclusion_tree.topLevelItem(0)
    assert dirs_item.child(0).text(1) == relative_path

def test_rapid_operations(exclusions_ui, qtbot):
    """Test UI stability during rapid operations"""
    add_dir_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                      if btn.text() == 'Add Directory')
    
    for _ in range(10):
        qtbot.mouseClick(add_dir_btn, Qt.LeftButton)
        qtbot.wait(50)
    
    qtbot.wait(200)
    assert exclusions_ui.exclusion_tree.topLevelItemCount() > 0

def test_invalid_project_context(exclusions_ui, qtbot):
    """Test handling of invalid project context"""
    # Set invalid project context
    exclusions_ui.controller.project_controller.project_context.is_initialized = False
    
    # Trigger load
    exclusions_ui.load_project_data()
    qtbot.wait(100)
    
    # Verify empty trees
    assert exclusions_ui.exclusion_tree.topLevelItemCount() == 0
    assert exclusions_ui.root_tree.topLevelItemCount() == 0

def test_save_and_exit_error_handling(exclusions_ui, qtbot, mocker):
    """Test error handling in save and exit"""
    # Mock error in save_settings
    exclusions_ui.settings_manager.save_settings.side_effect = Exception("Test error")
    mock_warning = mocker.patch.object(QMessageBox, 'warning')
    
    # Setup some test data
    test_data = {
        'root_exclusions': {'root1'},
        'excluded_dirs': {'dir1'},
        'excluded_files': {'file1.txt'}
    }
    exclusions_ui.settings_manager.update_settings(test_data)
    exclusions_ui.populate_exclusion_tree()
    
    # Try to save
    save_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                   if btn.text() == 'Save & Exit')
    qtbot.mouseClick(save_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    # Verify error handling
    mock_warning.assert_called_once()
    assert "Test error" in mock_warning.call_args[0][2]

def test_remove_selected_multiple(exclusions_ui, qtbot):
    """Test removing multiple selected items"""
    # Setup test data with multiple items
    test_data = {
        'excluded_dirs': {'dir1', 'dir2'},
        'excluded_files': {'file1.txt', 'file2.txt'},
        'root_exclusions': set()
    }
    exclusions_ui.settings_manager.update_settings(test_data)
    exclusions_ui.populate_exclusion_tree()
    
    # Select multiple items
    dirs_item = exclusions_ui.exclusion_tree.topLevelItem(0)
    files_item = exclusions_ui.exclusion_tree.topLevelItem(1)
    
    # Enable multi-selection mode
    exclusions_ui.exclusion_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
    
    # Select items properly
    dirs_item.child(0).setSelected(True)
    files_item.child(0).setSelected(True)
    qtbot.wait(100)
    
    # Remove selected
    remove_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                     if btn.text() == 'Remove Selected')
    qtbot.mouseClick(remove_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    # Verify both items were removed
    current_data = exclusions_ui.settings_manager.get_all_exclusions()
    assert len(current_data['excluded_dirs']) == 1
    assert len(current_data['excluded_files']) == 1

def test_add_file_in_root_exclusion(exclusions_ui, qtbot, mocker):
    """Test attempting to add a file within a root exclusion"""
    # Setup root exclusion
    test_data = {
        'root_exclusions': {'subfolder'},
        'excluded_dirs': set(),
        'excluded_files': set()
    }
    exclusions_ui.settings_manager.update_settings(test_data)
    
    # Mock file dialog to return a file within root exclusion
    mocker.patch.object(QFileDialog, 'getOpenFileName', 
                       return_value=("/test/project/subfolder/test.txt", ""))
    mock_warning = mocker.patch.object(QMessageBox, 'warning')
    
    # Try to add file
    add_file_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                       if btn.text() == 'Add File')
    qtbot.mouseClick(add_file_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    # Verify warning and no change
    mock_warning.assert_called_once()
    current_data = exclusions_ui.settings_manager.get_all_exclusions()
    assert len(current_data['excluded_files']) == 0

def test_edit_item(exclusions_ui, qtbot):
    """Test editing an excluded item"""
    # Setup initial data
    test_data = {
        'excluded_dirs': {'dir1'},
        'excluded_files': set(),
        'root_exclusions': set()
    }
    exclusions_ui.settings_manager.update_settings(test_data)
    exclusions_ui.populate_exclusion_tree()
    
    # Edit the item
    dirs_item = exclusions_ui.exclusion_tree.topLevelItem(0)
    test_item = dirs_item.child(0)
    test_item.setText(1, 'new_dir')
    
    # Save changes
    save_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                   if btn.text() == 'Save & Exit')
    qtbot.mouseClick(save_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    # Verify changes were saved
    current_data = exclusions_ui.settings_manager.get_all_exclusions()
    assert 'new_dir' in current_data['excluded_dirs']
    assert 'dir1' not in current_data['excluded_dirs']

def test_project_context_null(exclusions_ui, qtbot):
    """Test handling of null project context"""
    # Set null project context
    exclusions_ui.controller.project_controller.project_context = None
    
    # Trigger load
    exclusions_ui.load_project_data()
    qtbot.wait(100)
    
    # Verify warning shown and empty trees
    assert exclusions_ui.exclusion_tree.topLevelItemCount() == 0
    assert exclusions_ui.root_tree.topLevelItemCount() == 0

def test_add_directory_cancelled(exclusions_ui, qtbot, mocker):
    """Test cancelling directory addition"""
    # Mock dialog to return empty string (cancelled)
    mocker.patch.object(QFileDialog, 'getExistingDirectory', return_value="")
    
    initial_count = len(exclusions_ui.settings_manager.get_all_exclusions()['excluded_dirs'])
    
    # Try to add directory
    add_dir_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                      if btn.text() == 'Add Directory')
    qtbot.mouseClick(add_dir_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    # Verify no changes
    current_count = len(exclusions_ui.settings_manager.get_all_exclusions()['excluded_dirs'])
    assert current_count == initial_count

def test_add_file_cancelled(exclusions_ui, qtbot, mocker):
    """Test cancelling file addition"""
    # Mock dialog to return empty string (cancelled)
    mocker.patch.object(QFileDialog, 'getOpenFileName', return_value=("", ""))
    
    initial_count = len(exclusions_ui.settings_manager.get_all_exclusions()['excluded_files'])
    
    # Try to add file
    add_file_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                       if btn.text() == 'Add File')
    qtbot.mouseClick(add_file_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    # Verify no changes
    current_count = len(exclusions_ui.settings_manager.get_all_exclusions()['excluded_files'])
    assert current_count == initial_count

def test_remove_selected_none_selected(exclusions_ui, qtbot, mocker):
    """Test remove selected with no selection"""
    mock_info = mocker.patch.object(QMessageBox, 'information')
    
    # Try to remove without selection
    remove_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                     if btn.text() == 'Remove Selected')
    qtbot.mouseClick(remove_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    # Verify information dialog shown
    mock_info.assert_called_once()
    assert "No Selection" in mock_info.call_args[0][1]

def test_save_and_exit_null_children(exclusions_ui, qtbot):
    """Test save and exit with null tree items"""
    # Clear trees
    exclusions_ui.exclusion_tree.clear()
    exclusions_ui.root_tree.clear()
    
    # Try to save
    save_btn = next(btn for btn in exclusions_ui.findChildren(QPushButton)
                   if btn.text() == 'Save & Exit')
    qtbot.mouseClick(save_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    # Verify empty lists saved
    saved_data = exclusions_ui.settings_manager.get_all_exclusions()
    assert len(saved_data['root_exclusions']) == 0
    assert len(saved_data['excluded_dirs']) == 0
    assert len(saved_data['excluded_files']) == 0