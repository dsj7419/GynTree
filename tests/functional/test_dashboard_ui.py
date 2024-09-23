import pytest
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from components.UI.DashboardUI import DashboardUI
from controllers.AppController import AppController
from utilities.theme_manager import ThemeManager

pytestmark = pytest.mark.functional

@pytest.fixture(scope="module")
def app():
    return QApplication([])

@pytest.fixture
def dashboard_ui(app):
    controller = AppController()
    return DashboardUI(controller)

def test_initialization(dashboard_ui):
    assert dashboard_ui.controller is not None
    assert dashboard_ui.theme_manager is not None
    assert dashboard_ui.theme_toggle is not None

def test_create_styled_button(dashboard_ui):
    button = dashboard_ui.create_styled_button("Test Button")
    assert button.text() == "Test Button"
    assert button.font().pointSize() == 14

def test_toggle_theme(dashboard_ui, mocker):
    mock_toggle_theme = mocker.patch.object(dashboard_ui.controller, 'toggle_theme')
    dashboard_ui.toggle_theme()
    mock_toggle_theme.assert_called_once()

def test_show_dashboard(dashboard_ui, mocker):
    mock_show = mocker.patch.object(dashboard_ui, 'show')
    dashboard_ui.show_dashboard()
    mock_show.assert_called_once()

def test_show_project_ui(dashboard_ui, mocker):
    mock_project_ui = mocker.Mock()
    mock_show = mocker.patch.object(mock_project_ui, 'show')
    mocker.patch('components.UI.project_ui.ProjectUI', return_value=mock_project_ui)
    result = dashboard_ui.show_project_ui()
    assert result == mock_project_ui
    mock_show.assert_called_once()

def test_on_project_created(dashboard_ui, mocker):
    mock_project = mocker.Mock()
    mock_update_project_info = mocker.patch.object(dashboard_ui, 'update_project_info')
    mock_enable_project_actions = mocker.patch.object(dashboard_ui, 'enable_project_actions')
    dashboard_ui.on_project_created(mock_project)
    mock_update_project_info.assert_called_once_with(mock_project)
    mock_enable_project_actions.assert_called_once()

def test_on_project_loaded(dashboard_ui, mocker):
    mock_project = mocker.Mock()
    mock_update_project_info = mocker.patch.object(dashboard_ui, 'update_project_info')
    mock_enable_project_actions = mocker.patch.object(dashboard_ui, 'enable_project_actions')
    dashboard_ui.on_project_loaded(mock_project)
    mock_update_project_info.assert_called_once_with(mock_project)
    mock_enable_project_actions.assert_called_once()

def test_enable_project_actions(dashboard_ui):
    dashboard_ui.enable_project_actions()
    assert dashboard_ui.manage_exclusions_btn.isEnabled()
    assert dashboard_ui.analyze_directory_btn.isEnabled()
    assert dashboard_ui.view_directory_tree_btn.isEnabled()

def test_show_auto_exclude_ui(dashboard_ui, mocker):
    mock_auto_exclude_ui = mocker.Mock()
    mocker.patch('components.UI.auto_exclude_ui.AutoExcludeUI', return_value=mock_auto_exclude_ui)
    result = dashboard_ui.show_auto_exclude_ui(None, None, [], None)
    assert result == mock_auto_exclude_ui
    mock_auto_exclude_ui.show.assert_called_once()

def test_show_result(dashboard_ui, mocker):
    mock_result_ui = mocker.Mock()
    mocker.patch('components.UI.result_ui.ResultUI', return_value=mock_result_ui)
    result = dashboard_ui.show_result(None)
    assert result == mock_result_ui
    mock_result_ui.show.assert_called_once()

def test_manage_exclusions(dashboard_ui, mocker):
    mock_exclusions_ui = mocker.Mock()
    mocker.patch('components.UI.exclusions_manager_ui.ExclusionsManagerUI', return_value=mock_exclusions_ui)
    result = dashboard_ui.manage_exclusions(None)
    assert result == mock_exclusions_ui
    mock_exclusions_ui.show.assert_called_once()

def test_view_directory_tree_ui(dashboard_ui, mocker):
    mock_directory_tree_ui = mocker.Mock()
    mocker.patch('components.UI.directory_tree_ui.DirectoryTreeUI', return_value=mock_directory_tree_ui)
    dashboard_ui.view_directory_tree_ui({})
    mock_directory_tree_ui.update_tree.assert_called_once_with({})
    mock_directory_tree_ui.show.assert_called_once()

def test_update_project_info(dashboard_ui, mocker):
    mock_project = mocker.Mock(name="Test Project", start_directory="/test/path")
    mock_set_window_title = mocker.patch.object(dashboard_ui, 'setWindowTitle')
    mock_show_message = mocker.patch.object(dashboard_ui.status_bar, 'showMessage')
    dashboard_ui.update_project_info(mock_project)
    mock_set_window_title.assert_called_once_with("GynTree - Test Project")
    mock_show_message.assert_called_once_with("Current project: Test Project, Start directory: /test/path")

def test_clear_directory_tree(dashboard_ui, mocker):
    mock_clear = mocker.Mock()
    dashboard_ui.directory_tree_view = mocker.Mock(clear=mock_clear)
    dashboard_ui.clear_directory_tree()
    mock_clear.assert_called_once()

def test_clear_analysis(dashboard_ui, mocker):
    mock_clear = mocker.Mock()
    dashboard_ui.analysis_result_view = mocker.Mock(clear=mock_clear)
    dashboard_ui.clear_analysis()
    mock_clear.assert_called_once()

def test_clear_exclusions(dashboard_ui, mocker):
    mock_clear = mocker.Mock()
    dashboard_ui.exclusions_list_view = mocker.Mock(clear=mock_clear)
    dashboard_ui.clear_exclusions()
    mock_clear.assert_called_once()

def test_show_error_message(dashboard_ui, mocker):
    mock_critical = mocker.patch('PyQt5.QtWidgets.QMessageBox.critical')
    dashboard_ui.show_error_message("Test Title", "Test Message")
    mock_critical.assert_called_once_with(dashboard_ui, "Test Title", "Test Message")

def test_theme_toggle_state(dashboard_ui):
    assert dashboard_ui.theme_toggle.isChecked() == (dashboard_ui.theme_manager.get_current_theme() == 'dark')

def test_theme_toggle_connection(dashboard_ui, qtbot):
    with qtbot.waitSignal(dashboard_ui.theme_toggle.stateChanged, timeout=1000):
        dashboard_ui.theme_toggle.setChecked(not dashboard_ui.theme_toggle.isChecked())

def test_apply_theme(dashboard_ui, mocker):
    mock_apply_theme = mocker.patch.object(dashboard_ui.theme_manager, 'apply_theme')
    dashboard_ui.apply_theme()
    mock_apply_theme.assert_called_once_with(dashboard_ui)

def test_button_connections(dashboard_ui):
    assert dashboard_ui.create_project_btn.clicked.connect.called
    assert dashboard_ui.load_project_btn.clicked.connect.called
    assert dashboard_ui.manage_exclusions_btn.clicked.connect.called
    assert dashboard_ui.analyze_directory_btn.clicked.connect.called
    assert dashboard_ui.view_directory_tree_btn.clicked.connect.called

def test_initial_button_states(dashboard_ui):
    assert dashboard_ui.manage_exclusions_btn.isEnabled()
    assert dashboard_ui.analyze_directory_btn.isEnabled()
    assert dashboard_ui.view_directory_tree_btn.isEnabled()

def test_theme_toggle_initial_state(dashboard_ui):
    assert dashboard_ui.theme_toggle.isChecked() == (dashboard_ui.theme_manager.get_current_theme() == 'dark')

def test_status_bar_initial_state(dashboard_ui):
    assert dashboard_ui.status_bar.currentMessage() == "Ready"

def test_window_title(dashboard_ui):
    assert dashboard_ui.windowTitle() == "GynTree Dashboard"

def test_main_layout_margins(dashboard_ui):
    main_layout = dashboard_ui.centralWidget().layout()
    assert main_layout.contentsMargins() == (30, 30, 30, 30)

def test_main_layout_spacing(dashboard_ui):
    main_layout = dashboard_ui.centralWidget().layout()
    assert main_layout.spacing() == 20

def test_logo_label(dashboard_ui):
    logo_label = dashboard_ui.findChild(QLabel, "logo_label")
    assert logo_label is not None
    assert not logo_label.pixmap().isNull()

def test_welcome_label(dashboard_ui):
    welcome_label = dashboard_ui.findChild(QLabel, "welcome_label")
    assert welcome_label is not None
    assert welcome_label.text() == "Welcome to GynTree!"
    assert welcome_label.font().pointSize() == 24
    assert welcome_label.font().weight() == QFont.Bold

def test_theme_toggle_size(dashboard_ui):
    assert dashboard_ui.theme_toggle.size() == dashboard_ui.theme_toggle.sizeHint()

def test_button_styles(dashboard_ui):
    buttons = [
        dashboard_ui.create_project_btn,
        dashboard_ui.load_project_btn,
        dashboard_ui.manage_exclusions_btn,
        dashboard_ui.analyze_directory_btn,
        dashboard_ui.view_directory_tree_btn
    ]
    for button in buttons:
        assert button.font().pointSize() == 14

def test_window_geometry(dashboard_ui):
    geometry = dashboard_ui.geometry()
    assert geometry.width() == 800
    assert geometry.height() == 600