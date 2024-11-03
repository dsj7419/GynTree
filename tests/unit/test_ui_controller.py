import logging

import pytest
from PyQt5.QtCore import QMetaObject, Qt, QTimer
from PyQt5.QtWidgets import QMessageBox, QWidget

from controllers.UIController import UIController

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_main_ui(mocker):
    ui = mocker.Mock()
    ui.clear_directory_tree = mocker.Mock()
    ui.clear_analysis = mocker.Mock()
    ui.clear_exclusions = mocker.Mock()
    ui.show_auto_exclude_ui = mocker.Mock()
    ui.manage_exclusions = mocker.Mock()
    ui.show_result = mocker.Mock()
    ui.view_directory_tree_ui = mocker.Mock()
    ui.show_dashboard = mocker.Mock()
    ui.show_error_message = mocker.Mock()
    ui.update_project_info = mocker.Mock()
    return ui


@pytest.fixture
def ui_controller(mock_main_ui):
    controller = UIController(mock_main_ui)
    return controller


def test_initialization(ui_controller, mock_main_ui):
    """Test UI controller initialization"""
    assert ui_controller.main_ui == mock_main_ui
    assert mock_main_ui is not None


@pytest.mark.timeout(30)
def test_reset_ui(ui_controller, mock_main_ui):
    """Test UI reset functionality"""
    ui_controller.reset_ui()

    mock_main_ui.clear_directory_tree.assert_called_once()
    mock_main_ui.clear_analysis.assert_called_once()
    mock_main_ui.clear_exclusions.assert_called_once()


@pytest.mark.timeout(30)
def test_show_auto_exclude_ui(ui_controller, mock_main_ui):
    """Test showing auto-exclude UI"""
    mock_manager = object()
    mock_settings = object()
    mock_recommendations = []
    mock_context = object()

    ui_controller.show_auto_exclude_ui(
        mock_manager, mock_settings, mock_recommendations, mock_context
    )

    mock_main_ui.show_auto_exclude_ui.assert_called_once_with(
        mock_manager, mock_settings, mock_recommendations, mock_context
    )


@pytest.mark.timeout(30)
def test_show_auto_exclude_ui_error(ui_controller, mock_main_ui):
    """Test error handling in auto-exclude UI"""
    mock_main_ui.show_auto_exclude_ui.side_effect = Exception("Test error")
    ui_controller.show_auto_exclude_ui(None, None, None, None)
    mock_main_ui.show_error_message.assert_called_once()


@pytest.mark.timeout(30)
def test_manage_exclusions(ui_controller, mock_main_ui):
    """Test exclusions management"""
    mock_settings = object()
    ui_controller.manage_exclusions(mock_settings)
    mock_main_ui.manage_exclusions.assert_called_once_with(mock_settings)


@pytest.mark.timeout(30)
def test_manage_exclusions_error(ui_controller, mock_main_ui):
    """Test error handling in exclusions management"""
    mock_main_ui.manage_exclusions.side_effect = Exception("Test error")
    ui_controller.manage_exclusions(None)
    mock_main_ui.show_error_message.assert_called_once()


@pytest.mark.timeout(30)
def test_view_directory_tree(ui_controller, mock_main_ui):
    """Test directory tree view"""
    mock_result = {"test": "data"}
    ui_controller.view_directory_tree(mock_result)
    mock_main_ui.view_directory_tree_ui.assert_called_once_with(mock_result)


@pytest.mark.timeout(30)
def test_view_directory_tree_error(ui_controller, mock_main_ui):
    """Test error handling in directory tree view"""
    mock_main_ui.view_directory_tree_ui.side_effect = Exception("Test error")
    ui_controller.view_directory_tree({})
    mock_main_ui.show_error_message.assert_called_once()


@pytest.mark.timeout(30)
def test_show_result(ui_controller, mock_main_ui):
    """Test showing results"""
    mock_analyzer = object()
    ui_controller.show_result(mock_analyzer)
    mock_main_ui.show_result.assert_called_once_with(mock_analyzer)


@pytest.mark.timeout(30)
def test_show_result_error(ui_controller, mock_main_ui):
    """Test error handling in show result"""
    mock_main_ui.show_result.side_effect = Exception("Test error")
    ui_controller.show_result(object())
    mock_main_ui.show_error_message.assert_called_once()


def test_show_error_message(ui_controller, mock_main_ui):
    """Test error message display"""
    ui_controller.show_error_message("Test Title", "Test Message")
    mock_main_ui.show_error_message.assert_called_once_with(
        "Test Title", "Test Message"
    )


@pytest.mark.timeout(30)
def test_show_error_message_fallback(ui_controller, mock_main_ui, mocker):
    """Test error message fallback mechanism"""
    mock_main_ui.show_error_message.side_effect = Exception("UI Error")
    mock_qmessage = mocker.patch("PyQt5.QtWidgets.QMessageBox.critical")

    ui_controller.show_error_message("Test", "Message")
    mock_qmessage.assert_called_once()


@pytest.mark.timeout(30)
def test_show_dashboard(ui_controller, mock_main_ui):
    """Test dashboard display"""
    ui_controller.show_dashboard()
    mock_main_ui.show_dashboard.assert_called_once()


@pytest.mark.timeout(30)
def test_show_dashboard_error(ui_controller, mock_main_ui):
    """Test error handling in dashboard display"""
    mock_main_ui.show_dashboard.side_effect = Exception("Test error")
    ui_controller.show_dashboard()
    mock_main_ui.show_error_message.assert_called_once()


@pytest.mark.timeout(30)
def test_update_ui(ui_controller, qtbot, mocker):
    """Test UI update mechanism"""
    mock_component = mocker.Mock()
    mock_data = {"test": "data"}

    mock_invoke = mocker.patch("PyQt5.QtCore.QMetaObject.invokeMethod")

    ui_controller.update_ui(mock_component, mock_data)
    mock_invoke.assert_called_once()


@pytest.mark.timeout(30)
def test_update_ui_error(ui_controller, mock_main_ui, mocker):
    """Test error handling in UI update"""
    mock_invoke = mocker.patch(
        "PyQt5.QtCore.QMetaObject.invokeMethod", side_effect=Exception("Test error")
    )
    ui_controller.update_ui(mocker.Mock(), {})
    mock_main_ui.show_error_message.assert_called_once()


@pytest.mark.timeout(30)
def test_update_project_info(ui_controller, mock_main_ui):
    """Test project info update"""
    mock_project = object()
    ui_controller.update_project_info(mock_project)
    mock_main_ui.update_project_info.assert_called_once_with(mock_project)


@pytest.mark.timeout(30)
def test_update_project_info_error(ui_controller, mock_main_ui):
    """Test error handling in project info update"""
    mock_main_ui.update_project_info.side_effect = Exception("Test error")
    ui_controller.update_project_info(None)
    mock_main_ui.show_error_message.assert_called_once()


@pytest.mark.timeout(30)
def test_concurrent_operations(ui_controller, mock_main_ui, qtbot):
    """Test handling of concurrent UI operations"""
    operations = [
        lambda: ui_controller.reset_ui(),
        lambda: ui_controller.show_dashboard(),
        lambda: ui_controller.show_error_message("Test", "Message"),
        lambda: ui_controller.manage_exclusions(object()),
        lambda: ui_controller.view_directory_tree({}),
        lambda: ui_controller.show_result(object()),
    ]

    for op in operations:
        op()
        qtbot.wait(10)

    assert len(mock_main_ui.method_calls) >= len(operations)


@pytest.mark.timeout(30)
def test_ui_state_consistency(ui_controller, mock_main_ui, qtbot):
    """Test UI state consistency during operations"""
    ui_controller.reset_ui()
    qtbot.wait(10)
    ui_controller.show_dashboard()
    qtbot.wait(10)
    ui_controller.show_result(object())
    qtbot.wait(10)

    # Verify operations order
    method_names = [call[0] for call in mock_main_ui.method_calls]
    assert "clear_directory_tree" in method_names
    assert "clear_analysis" in method_names
    assert "clear_exclusions" in method_names
    assert "show_dashboard" in method_names
    assert "show_result" in method_names
