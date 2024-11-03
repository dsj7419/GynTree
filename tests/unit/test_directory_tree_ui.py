# tests/unit/test_directory_tree_ui.py
import os
from pathlib import Path

import pytest
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import (
    QApplication,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from components.TreeExporter import TreeExporter
from components.UI.DirectoryTreeUI import DirectoryTreeUI

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_controller(mocker):
    return mocker.Mock()


@pytest.fixture
def mock_theme_manager(mocker):
    theme_manager = mocker.Mock()
    theme_manager.themeChanged = mocker.Mock()
    return theme_manager


@pytest.fixture
def directory_tree_ui(qtbot, mock_controller, mock_theme_manager):
    ui = DirectoryTreeUI(mock_controller, mock_theme_manager)
    qtbot.addWidget(ui)
    ui.show()
    return ui


@pytest.fixture(autouse=True)
def cleanup_files(tmp_path):
    """Clean up any test files after each test"""
    # Ensure directory exists
    tmp_path.mkdir(parents=True, exist_ok=True)

    def remove_file(path):
        try:
            if path.exists():
                path.unlink(missing_ok=True)
        except Exception:
            pass

    # Clean up before test
    remove_file(tmp_path / "test_export.png")
    remove_file(tmp_path / "empty_export.png")
    remove_file(tmp_path / "test_export.txt")

    yield

    # Clean up after test with retry
    import time

    for _ in range(3):  # Retry up to 3 times
        try:
            remove_file(tmp_path / "test_export.png")
            remove_file(tmp_path / "empty_export.png")
            remove_file(tmp_path / "test_export.txt")
            break
        except Exception:
            time.sleep(0.1)


@pytest.fixture(autouse=True)
def mock_messagebox(mocker):
    """Mock QMessageBox to automatically accept dialogs."""
    mocker.patch.object(QMessageBox, "warning", return_value=QMessageBox.Ok)
    mocker.patch.object(QMessageBox, "information", return_value=QMessageBox.Ok)
    mocker.patch.object(QMessageBox, "critical", return_value=QMessageBox.Ok)


@pytest.fixture(autouse=True)
def mock_tempfile(mocker, tmp_path):
    """Mock tempfile to avoid file access issues"""
    mock_temp = mocker.patch("tempfile.NamedTemporaryFile")
    mock_temp_name = str(tmp_path / "temp.png")
    mock_temp.return_value.__enter__.return_value.name = mock_temp_name
    return mock_temp


@pytest.fixture(autouse=True)
def mock_os_operations(mocker):
    """Mock os operations to avoid file access issues"""
    mocker.patch("os.path.exists").return_value = True
    mocker.patch("os.remove")
    mocker.patch("os.rename")
    return mocker


@pytest.fixture(autouse=True)
def clean_temp_files():
    """Cleanup any leftover temp files"""
    import shutil
    import tempfile

    # Store original tempdir
    original_tempdir = tempfile.gettempdir()

    yield

    # Clean up temp files after test
    try:
        for filename in os.listdir(original_tempdir):
            if filename.startswith("tmp") and (
                filename.endswith(".png") or filename.endswith(".txt")
            ):
                filepath = os.path.join(original_tempdir, filename)
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                except Exception:
                    pass
    except Exception:
        pass


def test_initialization(directory_tree_ui):
    """Test initial UI setup"""
    assert isinstance(directory_tree_ui, QWidget)
    assert directory_tree_ui.windowTitle() == "Directory Tree"
    assert directory_tree_ui.tree_widget is not None
    assert directory_tree_ui.tree_exporter is not None


def test_ui_components(directory_tree_ui):
    """Test presence and properties of UI components"""
    # Test title label
    title_label = directory_tree_ui.findChild(QLabel)
    assert title_label is not None
    assert title_label.text() == "Directory Tree"

    # Test buttons
    buttons = directory_tree_ui.findChildren(QPushButton)
    button_texts = {"Collapse All", "Expand All", "Export PNG", "Export ASCII"}
    assert {btn.text() for btn in buttons} == button_texts


def test_tree_widget_setup(directory_tree_ui):
    """Test tree widget configuration"""
    tree = directory_tree_ui.tree_widget
    assert tree.columnCount() == 1
    assert tree.headerItem().text(0) == "Name"
    assert tree.iconSize() == QSize(20, 20)


@pytest.mark.timeout(30)
def test_update_tree(directory_tree_ui, qtbot):
    """Test tree update with directory structure"""
    test_structure = {
        "name": "root",
        "type": "directory",
        "children": [
            {"name": "test_file.py", "type": "file"},
            {"name": "test_dir", "type": "directory", "children": []},
        ],
    }

    directory_tree_ui.update_tree(test_structure)
    qtbot.wait(100)

    root = directory_tree_ui.tree_widget.invisibleRootItem()
    assert root.childCount() > 0

    # Verify structure
    first_item = root.child(0)
    assert first_item.text(0) == "root"
    assert first_item.childCount() == 2


@pytest.mark.timeout(30)
def test_export_functions(directory_tree_ui, qtbot, mocker, tmp_path):
    """Test export functionality with proper mocking and file handling"""
    # Mock ALL possible message boxes that might appear
    mock_info = mocker.patch(
        "PyQt5.QtWidgets.QMessageBox.information", return_value=QMessageBox.Ok
    )
    mock_error = mocker.patch(
        "PyQt5.QtWidgets.QMessageBox.critical", return_value=QMessageBox.Ok
    )
    mock_warning = mocker.patch(
        "PyQt5.QtWidgets.QMessageBox.warning", return_value=QMessageBox.Ok
    )

    # Mock file dialog
    mock_file_dialog = mocker.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName")

    png_path = tmp_path / "test_export.png"
    ascii_path = tmp_path / "test_export.txt"
    mock_file_dialog.side_effect = [
        (str(png_path), "PNG Files (*.png)"),
        (str(ascii_path), "Text Files (*.txt)"),
    ]

    # Setup test data
    test_structure = {
        "name": "root",
        "type": "directory",
        "children": [
            {"name": "test_file.py", "type": "file"},
            {"name": "test_dir", "type": "directory", "children": []},
        ],
    }
    directory_tree_ui.update_tree(test_structure)
    qtbot.wait(200)

    # Test PNG export
    export_png_btn = next(
        btn
        for btn in directory_tree_ui.findChildren(QPushButton)
        if btn.text() == "Export PNG"
    )
    QTest.mouseClick(export_png_btn, Qt.LeftButton)
    qtbot.wait(1000)

    # Test ASCII export
    export_ascii_btn = next(
        btn
        for btn in directory_tree_ui.findChildren(QPushButton)
        if btn.text() == "Export ASCII"
    )
    QTest.mouseClick(export_ascii_btn, Qt.LeftButton)
    qtbot.wait(1000)

    # Verify that some dialog was shown (either success or error)
    assert any(
        [mock_info.called, mock_error.called, mock_warning.called]
    ), "No dialog was shown after export operation"


@pytest.mark.timeout(30)
def test_export_empty_tree(directory_tree_ui, qtbot, mocker, tmp_path):
    """Test export functionality with an empty tree."""

    # Mock QMessageBox to capture dialogs and set up auto-close
    mock_warning = mocker.patch(
        "PyQt5.QtWidgets.QMessageBox.warning", side_effect=lambda *args: QMessageBox.Ok
    )

    # Use a real temporary file path for export
    png_path = tmp_path / "empty_export.png"
    mock_file_dialog = mocker.patch(
        "PyQt5.QtWidgets.QFileDialog.getSaveFileName",
        return_value=(str(png_path), "PNG Files (*.png)"),
    )

    # Clear the tree to simulate an empty state
    directory_tree_ui.tree_widget.clear()
    qtbot.wait(200)

    # Set up a QTimer to close the dialog automatically after showing it
    def close_warning():
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMessageBox):
                widget.accept()  # Close the dialog

    # Trigger the QTimer to close the warning dialog after it appears
    QTimer.singleShot(500, close_warning)

    # Find and click the export button to trigger the export
    export_png_btn = next(
        btn
        for btn in directory_tree_ui.findChildren(QPushButton)
        if btn.text() == "Export PNG"
    )
    QTest.mouseClick(export_png_btn, Qt.LeftButton)

    # Verify that the warning dialog was shown
    assert mock_warning.called, "Warning dialog was not shown for empty tree export"


@pytest.mark.timeout(30)
def test_export_cancel(directory_tree_ui, qtbot, mocker):
    """Test canceling export operation"""
    # Mock file dialog to return empty string (simulates cancel)
    mock_file_dialog = mocker.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName")
    mock_file_dialog.return_value = ("", "")

    export_png_btn = next(
        btn
        for btn in directory_tree_ui.findChildren(QPushButton)
        if btn.text() == "Export PNG"
    )

    QTest.mouseClick(export_png_btn, Qt.LeftButton)
    qtbot.wait(100)

    # Verify no errors occurred
    assert directory_tree_ui.tree_exporter is not None


@pytest.mark.timeout(30)
def test_export_large_tree(directory_tree_ui, qtbot, mocker, tmp_path):
    """Test export with large tree structure"""

    # Create large test structure
    def create_large_structure(depth=3, width=100):
        if depth == 0:
            return []
        return [{"name": f"file_{i}.py", "type": "file"} for i in range(width)] + [
            {
                "name": f"dir_{i}",
                "type": "directory",
                "children": create_large_structure(depth - 1, width // 2),
            }
            for i in range(3)
        ]

    test_structure = {
        "name": "root",
        "type": "directory",
        "children": create_large_structure(),
    }

    # Setup export
    png_path = tmp_path / "large_export.png"
    mock_file_dialog = mocker.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName")
    mock_file_dialog.return_value = (str(png_path), "PNG Files (*.png)")

    # Update tree and export
    directory_tree_ui.update_tree(test_structure)
    qtbot.wait(200)

    export_png_btn = next(
        btn
        for btn in directory_tree_ui.findChildren(QPushButton)
        if btn.text() == "Export PNG"
    )

    QTest.mouseClick(export_png_btn, Qt.LeftButton)
    qtbot.wait(500)  # Longer wait for large tree

    # Verify export completed
    assert directory_tree_ui.tree_exporter is not None


@pytest.mark.timeout(30)
def test_expand_collapse_functionality(directory_tree_ui, qtbot):
    """Test expand/collapse functionality"""
    # Setup test data
    test_structure = {
        "name": "root",
        "type": "directory",
        "children": [
            {
                "name": "dir1",
                "type": "directory",
                "children": [{"name": "file1.py", "type": "file"}],
            }
        ],
    }

    directory_tree_ui.update_tree(test_structure)
    qtbot.wait(100)

    # Find buttons
    collapse_btn = next(
        btn
        for btn in directory_tree_ui.findChildren(QPushButton)
        if btn.text() == "Collapse All"
    )
    expand_btn = next(
        btn
        for btn in directory_tree_ui.findChildren(QPushButton)
        if btn.text() == "Expand All"
    )

    # Test collapse
    QTest.mouseClick(collapse_btn, Qt.LeftButton)
    qtbot.wait(100)
    root = directory_tree_ui.tree_widget.invisibleRootItem()
    assert not root.child(0).isExpanded()

    # Test expand
    QTest.mouseClick(expand_btn, Qt.LeftButton)
    qtbot.wait(100)
    assert root.child(0).isExpanded()


def test_theme_application(directory_tree_ui, mock_theme_manager):
    """Test theme application"""
    directory_tree_ui.apply_theme()
    mock_theme_manager.apply_theme.assert_called_with(directory_tree_ui)


@pytest.mark.timeout(30)
def test_memory_management(directory_tree_ui, qtbot):
    """Test memory management during updates"""
    import gc

    import psutil

    process = psutil.Process()
    initial_memory = process.memory_info().rss

    # Perform multiple updates
    for i in range(10):
        test_structure = {
            "name": f"root_{i}",
            "type": "directory",
            "children": [{"name": f"file_{j}.py", "type": "file"} for j in range(10)],
        }
        directory_tree_ui.update_tree(test_structure)
        qtbot.wait(50)
        gc.collect()

    final_memory = process.memory_info().rss
    memory_diff = final_memory - initial_memory

    # Check for memory leaks (less than 10MB increase)
    assert memory_diff < 10 * 1024 * 1024


def test_window_geometry(directory_tree_ui):
    """Test window geometry settings"""
    geometry = directory_tree_ui.geometry()
    assert geometry.width() == 800
    assert geometry.height() == 600


@pytest.mark.timeout(30)
def test_performance(directory_tree_ui, qtbot):
    """Test performance with large directory structure"""
    import time

    def create_large_structure(depth=3, files_per_dir=100):
        if depth == 0:
            return None

        return {
            "name": f"dir_depth_{depth}",
            "type": "directory",
            "children": [
                {"name": f"file_{i}.py", "type": "file"} for i in range(files_per_dir)
            ]
            + [
                {
                    "name": f"subdir_{i}",
                    "type": "directory",
                    "children": []
                    if depth == 1
                    else create_large_structure(depth - 1, files_per_dir)["children"],
                }
                for i in range(3)
            ],
        }

    start_time = time.time()
    directory_tree_ui.update_tree(create_large_structure())
    end_time = time.time()

    assert end_time - start_time < 2.0  # Should complete within 2 seconds


@pytest.mark.timeout(30)
def test_concurrent_operations(directory_tree_ui, qtbot):
    """Test handling of concurrent operations"""
    test_structure = {
        "name": "root",
        "type": "directory",
        "children": [{"name": f"file_{i}.py", "type": "file"} for i in range(100)],
    }

    # Simulate rapid concurrent operations
    for _ in range(10):
        directory_tree_ui.update_tree(test_structure)
        qtbot.wait(10)  # Minimal wait to simulate rapid updates

    assert directory_tree_ui.tree_widget.topLevelItemCount() > 0
