# tests/unit/test_project_ui.py
import pytest
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QFileDialog,
    QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtTest import QTest, QSignalSpy
from pytest_mock import mocker
from components.UI.ProjectUI import ProjectUI
from models.Project import Project
import os

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_controller(mocker):
    controller = mocker.Mock()
    controller.project_controller.project_manager.list_projects.return_value = [
        'project1', 'project2'
    ]
    mock_project = mocker.Mock(spec=Project)
    mock_project.name = 'project1'
    mock_project.start_directory = '/mock/dir'
    controller.project_controller.load_project.return_value = mock_project
    return controller

@pytest.fixture
def project_ui(qtbot, mock_controller):
    ui = ProjectUI(mock_controller)
    qtbot.addWidget(ui)
    ui.show()
    return ui

def test_initialization(project_ui):
    """Test initial UI setup"""
    assert isinstance(project_ui, QWidget)
    assert project_ui.windowTitle() == 'Project Manager'
    assert project_ui.project_name_input is not None
    assert project_ui.project_list is not None
    assert project_ui.start_dir_label is not None

def test_ui_components(project_ui):
    """Test presence and properties of UI components"""
    # Test main section frames
    sections = [w for w in project_ui.findChildren(QFrame) 
               if w.objectName() in ("createSection", "loadSection")]
    assert len(sections) == 2  # Create and Load sections
    
    # Test labels
    labels = project_ui.findChildren(QLabel)
    expected_titles = {'Create New Project', 'Load Existing Project'}
    assert {label.text() for label in labels if label.font().pointSize() == 24} == expected_titles

@pytest.mark.timeout(30)
def test_select_directory(project_ui, qtbot, mocker):
    """Test directory selection"""
    mock_dir = "/test/project/path"
    mocker.patch.object(QFileDialog, 'getExistingDirectory', return_value=mock_dir)
    
    QTest.mouseClick(project_ui.start_dir_button, Qt.LeftButton)
    qtbot.wait(100)
    
    assert project_ui.start_dir_label.text() == mock_dir

@pytest.mark.timeout(30)
def test_create_project_validation(project_ui, qtbot, mocker):
    """Test project creation validation"""
    mock_warning = mocker.patch.object(QMessageBox, 'warning')
    
    # Test empty project name
    QTest.mouseClick(project_ui.create_project_btn, Qt.LeftButton)
    qtbot.wait(100)
    mock_warning.assert_called_once()
    mock_warning.reset_mock()
    
    # Test missing directory
    project_ui.project_name_input.setText("test_project")
    QTest.mouseClick(project_ui.create_project_btn, Qt.LeftButton)
    qtbot.wait(100)
    mock_warning.assert_called_once()

@pytest.mark.timeout(30)
def test_create_project_success(project_ui, qtbot, tmp_path):
    """Test successful project creation"""
    # Set up project details with real temp directory
    project_name = "test_project"
    project_ui.project_name_input.setText(project_name)
    project_ui.start_dir_label.setText(str(tmp_path))
    
    # Watch for signal
    with qtbot.waitSignal(project_ui.project_created, timeout=1000) as blocker:
        QTest.mouseClick(project_ui.create_project_btn, Qt.LeftButton)
    
    # Check signal emission
    signal_args = blocker.args
    assert len(signal_args) == 1
    created_project = signal_args[0]
    assert isinstance(created_project, Project)
    assert created_project.name == project_name
    assert created_project.start_directory == str(tmp_path)

@pytest.mark.timeout(30)
def test_load_project(project_ui, qtbot):
    """Test project loading"""
    # Select project from list
    project_ui.project_list.setCurrentRow(0)
    
    # Watch for signal
    with qtbot.waitSignal(project_ui.project_loaded, timeout=1000) as blocker:
        QTest.mouseClick(project_ui.load_project_btn, Qt.LeftButton)
    
    # Check signal emission
    signal_args = blocker.args
    assert len(signal_args) == 1
    loaded_project = signal_args[0]
    assert isinstance(loaded_project, Project)
    assert loaded_project.name == "project1"

@pytest.mark.timeout(30)
def test_load_project_no_selection(project_ui, qtbot, mocker):
    """Test project loading without selection"""
    mock_warning = mocker.patch.object(QMessageBox, 'warning')
    
    # Clear selection and try to load
    project_ui.project_list.clearSelection()
    QTest.mouseClick(project_ui.load_project_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    mock_warning.assert_called_once()

def test_theme_application(project_ui):
    """Test theme application"""
    assert hasattr(project_ui, 'theme_manager')
    assert hasattr(project_ui.theme_manager, 'apply_theme')

@pytest.mark.timeout(30)
def test_memory_management(project_ui, qtbot):
    """Test memory management during operations"""
    import gc
    import psutil
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Perform multiple operations
    for i in range(100):
        project_ui.project_name_input.setText(f"test_project_{i}")
        project_ui.start_dir_label.setText(f"/test/path_{i}")
        qtbot.wait(10)
        gc.collect()
    
    final_memory = process.memory_info().rss
    memory_diff = final_memory - initial_memory
    
    # Check for memory leaks (less than 10MB increase)
    assert memory_diff < 10 * 1024 * 1024

def test_window_geometry(project_ui):
    """Test window geometry settings"""
    geometry = project_ui.geometry()
    assert geometry.width() == 600
    assert geometry.height() == 600
    assert geometry.x() == 300
    assert geometry.y() == 300

@pytest.mark.timeout(30)
def test_rapid_input(project_ui, qtbot):
    """Test UI stability during rapid input"""
    text = "test_project_name"
    for char in text:
        QTest.keyClick(project_ui.project_name_input, char)
        qtbot.wait(10)
    
    assert project_ui.project_name_input.text() == text

@pytest.mark.timeout(30)
def test_project_name_validation(project_ui, qtbot, tmp_path, mocker):
    """Test project name validation"""
    mock_warning = mocker.patch.object(QMessageBox, 'warning')
    
    invalid_names = [
        "test/project",
        "test\\project",
        "test:project",
        "test*project",
        "test?project",
        "test\"project",
        "test<project",
        "test>project",
        "test|project"
    ]
    
    for name in invalid_names:
        project_ui.project_name_input.setText(name)
        project_ui.start_dir_label.setText(str(tmp_path))
        QTest.mouseClick(project_ui.create_project_btn, Qt.LeftButton)
        qtbot.wait(50)
        mock_warning.assert_called()
        mock_warning.reset_mock()

@pytest.mark.timeout(30)
def test_error_handling(project_ui, qtbot, tmp_path, mocker):
    """Test error handling in UI operations"""
    mock_warning = mocker.patch.object(QMessageBox, 'warning')
    
    # Mock path validation
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('os.access', return_value=True)
    mocker.patch('pathlib.Path.exists', return_value=True)
    
    # Mock project creation to raise exception
    mocker.patch.object(
        Project,
        '__init__',
        side_effect=Exception("Test error")
    )
    
    project_ui.project_name_input.setText("test_project")
    project_ui.start_dir_label.setText(str(tmp_path))
    
    QTest.mouseClick(project_ui.create_project_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    mock_warning.assert_called_with(
        project_ui,
        "Error", 
        "Failed to create project: Test error"
    )

@pytest.mark.timeout(30)
def test_concurrent_operations(project_ui, qtbot, tmp_path, mocker):
    """Test handling of concurrent operations"""
    mock_dir = str(tmp_path)
    mocker.patch.object(QFileDialog, 'getExistingDirectory', return_value=mock_dir)
    
    # Simulate rapid concurrent operations
    for i in range(10):
        QTest.mouseClick(project_ui.start_dir_button, Qt.LeftButton)
        project_ui.project_name_input.setText(f"test_project_{i}")
        QTest.mouseClick(project_ui.create_project_btn, Qt.LeftButton)
        project_ui.project_list.setCurrentRow(0)
        QTest.mouseClick(project_ui.load_project_btn, Qt.LeftButton)
        qtbot.wait(10)

def test_signal_connections(project_ui):
    """Test signal connections"""
    assert project_ui.start_dir_button.receivers(project_ui.start_dir_button.clicked) > 0
    assert project_ui.create_project_btn.receivers(project_ui.create_project_btn.clicked) > 0
    assert project_ui.load_project_btn.receivers(project_ui.load_project_btn.clicked) > 0

@pytest.mark.timeout(30)
def test_directory_access_error(project_ui, qtbot, tmp_path, mocker):
    """Test directory access error handling"""
    mock_warning = mocker.patch.object(QMessageBox, 'warning')
    mocker.patch('os.access', return_value=False)
    
    project_ui.project_name_input.setText("test_project")
    project_ui.start_dir_label.setText(str(tmp_path))
    
    QTest.mouseClick(project_ui.create_project_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    mock_warning.assert_called_with(
        project_ui,
        "Invalid Directory",
        "Directory is not accessible"
    )

@pytest.mark.timeout(30)
def test_file_operation_error(project_ui, qtbot, tmp_path, mocker):
    """Test file operation error handling"""
    mock_warning = mocker.patch.object(QMessageBox, 'warning')
    # Need to patch path exists BEFORE PermissionError
    mocker.patch('os.path.exists', return_value=True)  # Add this
    mocker.patch('os.path.isdir', return_value=True)   # Add this
    mocker.patch('os.access', return_value=True)       # Add this
    mocker.patch('pathlib.Path.exists', side_effect=PermissionError("Access denied"))
    
    project_ui.project_name_input.setText("test_project")
    project_ui.start_dir_label.setText(str(tmp_path))
    
    QTest.mouseClick(project_ui.create_project_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    mock_warning.assert_called_with(
        project_ui,
        "Invalid Directory",
        "Invalid directory path: Access denied"
    )

@pytest.mark.timeout(30)
def test_close_event_handler(project_ui, qtbot):
    """Test close event handling"""
    event = QCloseEvent()
    project_ui.closeEvent(event)
    assert event.isAccepted()

@pytest.mark.timeout(30)
def test_invalid_directory_path(project_ui, qtbot, mocker):
    """Test handling of invalid directory paths"""
    mock_warning = mocker.patch.object(QMessageBox, 'warning')
    project_ui.project_name_input.setText("test_project")
    project_ui.start_dir_label.setText("not/a/real/path/at/all")
    
    QTest.mouseClick(project_ui.create_project_btn, Qt.LeftButton)
    qtbot.wait(100)
    
    mock_warning.assert_called_with(
        project_ui, 
        "Invalid Directory",
        "Selected directory does not exist"
    )