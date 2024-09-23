import threading
import pytest
from PyQt5.QtWidgets import QApplication
from controllers.AppController import AppController
from utilities.theme_manager import ThemeManager
import logging

pytestmark = pytest.mark.unit

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def log_test(func):
    def wrapper(*args, **kwargs):
        logger.debug(f"Starting test: {func.__name__}")
        result = func(*args, **kwargs)
        logger.debug(f"Finished test: {func.__name__}")
        return result
    return wrapper

def run_with_timeout(func, args=(), kwargs={}, timeout=10):
    result = [None]
    exception = [None]
    def worker():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError(f"Test timed out after {timeout} seconds")
    if exception[0]:
        raise exception[0]
    return result[0]

@pytest.fixture(scope="module")
def app():
    return QApplication([])

@pytest.fixture
def app_controller(app, mocker):
    controller = AppController()
    mock_project_context = mocker.Mock()
    mock_project_context.auto_exclude_manager = mocker.Mock()
    controller.project_controller.project_context = mock_project_context
    return controller

@log_test
def test_initialization(app_controller):
    assert app_controller.main_ui is not None
    assert app_controller.theme_manager is not None
    assert app_controller.project_controller is not None
    assert app_controller.thread_controller is not None
    assert app_controller.ui_controller is not None

@log_test
def test_run(app_controller, mocker):
    mock_show_dashboard = mocker.patch.object(app_controller.main_ui, 'show_dashboard')
    app_controller.run()
    mock_show_dashboard.assert_called_once()

@log_test
def test_cleanup(app_controller, mocker):
    mock_thread_cleanup = mocker.patch.object(app_controller.thread_controller, 'cleanup_thread')
    mock_project_close = mocker.patch.object(app_controller.project_controller, 'close_project', create=True)
    mock_ui_close = mocker.patch.object(QApplication, 'closeAllWindows')
    
    run_with_timeout(app_controller.cleanup)
    
    mock_thread_cleanup.assert_called_once()
    if app_controller.project_controller and app_controller.project_controller.project_context:
        mock_project_close.assert_called_once()
    mock_ui_close.assert_called_once()

@log_test
def test_toggle_theme(app_controller, mocker):
    mock_toggle = mocker.patch.object(app_controller.theme_manager, 'toggle_theme')
    mock_set_preference = mocker.patch.object(app_controller, 'set_theme_preference')
    app_controller.toggle_theme()
    mock_toggle.assert_called_once()
    mock_set_preference.assert_called_once()

@log_test
@pytest.mark.gui
def test_apply_theme_to_all_windows(app_controller, mocker, app):
    mock_apply = mocker.patch.object(app_controller.theme_manager, 'apply_theme_to_all_windows')
    app_controller.apply_theme_to_all_windows('light')
    mock_apply.assert_called_once_with(app)

@log_test
def test_get_theme_preference(app_controller, mocker):
    mock_get_preference = mocker.patch.object(app_controller.project_controller, 'get_theme_preference', return_value='light')
    theme = app_controller.get_theme_preference()
    assert theme == 'light'
    mock_get_preference.assert_called_once()

@log_test
def test_set_theme_preference(app_controller, mocker):
    mock_set_preference = mocker.patch.object(app_controller.project_controller, 'set_theme_preference')
    app_controller.set_theme_preference('dark')
    mock_set_preference.assert_called_once_with('dark')

@log_test
def test_create_project_action(app_controller, mocker):
    mock_show_project_ui = mocker.patch.object(app_controller.main_ui, 'show_project_ui')
    app_controller.create_project_action()
    mock_show_project_ui.assert_called_once()

@log_test
def test_on_project_created(app_controller, mocker):
    mock_project = mocker.Mock()
    mock_create_project = mocker.patch.object(app_controller.project_controller, 'create_project', return_value=True)
    mock_update_project_info = mocker.patch.object(app_controller.main_ui, 'update_project_info')
    mock_after_project_loaded = mocker.patch.object(app_controller, 'after_project_loaded')
    app_controller.on_project_created(mock_project)
    assert mock_update_project_info.call_count == 1, "update_project_info should be called once."

@log_test
def test_load_project_action(app_controller, mocker):
    mock_show_project_ui = mocker.patch.object(app_controller.main_ui, 'show_project_ui')
    app_controller.load_project_action()
    mock_show_project_ui.assert_called_once()

@log_test
def test_on_project_loaded(app_controller, mocker):
    mock_project = mocker.Mock()
    mock_load_project = mocker.patch.object(app_controller.project_controller, 'load_project', return_value=mock_project)
    mock_update_project_info = mocker.patch.object(app_controller.main_ui, 'update_project_info')
    mock_after_project_loaded = mocker.patch.object(app_controller, 'after_project_loaded')
    app_controller.on_project_loaded(mock_project)
    mock_load_project.assert_called_once_with(mock_project.name)
    mock_update_project_info.assert_called_once_with(mock_project)
    mock_after_project_loaded.assert_called_once()

@log_test
def test_after_project_loaded(app_controller, mocker):
    mock_reset_ui = mocker.patch.object(app_controller.ui_controller, 'reset_ui')
    mock_start_auto_exclude = mocker.patch.object(app_controller, '_start_auto_exclude')
    app_controller.after_project_loaded()
    mock_reset_ui.assert_called_once()
    mock_start_auto_exclude.assert_called_once()

@log_test
def test_manage_exclusions(app_controller, mocker):
    mock_manage_exclusions = mocker.patch.object(app_controller.ui_controller, 'manage_exclusions')
    app_controller.manage_exclusions()
    mock_manage_exclusions.assert_called_once()

@log_test
def test_view_directory_tree(app_controller, mocker):
    mock_view_directory_tree = mocker.patch.object(app_controller.ui_controller, 'view_directory_tree')
    mock_project_context = mocker.Mock()
    mock_project_context.get_directory_tree = mocker.Mock(return_value={})
    app_controller.project_controller.project_context = mock_project_context
    app_controller.view_directory_tree()
    mock_project_context.get_directory_tree.assert_called_once()
    mock_view_directory_tree.assert_called_once_with({})

@log_test
def test_analyze_directory(app_controller, mocker):
    mock_show_result = mocker.patch.object(app_controller.ui_controller, 'show_result')
    mock_update_result = mocker.patch.object(mock_show_result.return_value, 'update_result')
    app_controller.analyze_directory()
    mock_show_result.assert_called_once()
    mock_update_result.assert_called_once()

@log_test
def test_start_auto_exclude(app_controller, mocker):
    mock_start_thread = mocker.patch.object(app_controller.thread_controller, 'start_auto_exclude_thread')
    app_controller._start_auto_exclude()
    mock_start_thread.assert_called_once_with(app_controller.project_controller.project_context)

@log_test
def test_on_auto_exclude_finished(app_controller, mocker):
    mock_show_auto_exclude_ui = mocker.patch.object(app_controller.main_ui, 'show_auto_exclude_ui')
    app_controller.project_controller.project_context.auto_exclude_manager = mocker.Mock()
    app_controller._on_auto_exclude_finished(['recommendation1', 'recommendation2'])
    mock_show_auto_exclude_ui.assert_called_once()

@log_test
def test_on_auto_exclude_error(app_controller, mocker):
    mock_show_dashboard = mocker.patch.object(app_controller.main_ui, 'show_dashboard')
    mock_critical = mocker.patch('PyQt5.QtWidgets.QMessageBox.critical')
    app_controller._on_auto_exclude_error("Test error")
    mock_critical.assert_called_once()
    mock_show_dashboard.assert_called_once()