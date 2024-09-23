import pytest
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt
from utilities.theme_manager import ThemeManager

pytestmark = pytest.mark.unit

@pytest.fixture(scope="module")
def app():
    return QApplication([])

@pytest.fixture
def theme_manager():
    return ThemeManager.getInstance()

def test_singleton_instance(theme_manager):
    assert ThemeManager.getInstance() is theme_manager

def test_initial_theme(theme_manager):
    assert theme_manager.get_current_theme() in ['light', 'dark']

def test_set_theme(theme_manager):
    initial_theme = theme_manager.get_current_theme()
    new_theme = 'dark' if initial_theme == 'light' else 'light'
    theme_manager.set_theme(new_theme)
    assert theme_manager.get_current_theme() == new_theme

def test_toggle_theme(theme_manager):
    initial_theme = theme_manager.get_current_theme()
    toggled_theme = theme_manager.toggle_theme()
    assert toggled_theme != initial_theme
    assert theme_manager.get_current_theme() == toggled_theme

def test_apply_theme(theme_manager, app):
    test_widget = QWidget()
    initial_style = test_widget.styleSheet()
    theme_manager.apply_theme(test_widget)
    assert test_widget.styleSheet() != initial_style

def test_apply_theme_to_all_windows(theme_manager, app):
    test_widget1 = QWidget()
    test_widget2 = QWidget()
    test_widget1.show()
    test_widget2.show()
    
    initial_style1 = test_widget1.styleSheet()
    initial_style2 = test_widget2.styleSheet()
    
    theme_manager.apply_theme_to_all_windows(app)
    
    assert test_widget1.styleSheet() != initial_style1
    assert test_widget2.styleSheet() != initial_style2

def test_theme_changed_signal(theme_manager, qtbot):
    with qtbot.waitSignal(theme_manager.themeChanged, timeout=1000) as blocker:
        theme_manager.toggle_theme()
    assert blocker.signal_triggered

def test_invalid_theme_setting(theme_manager):
    with pytest.raises(ValueError):
        theme_manager.set_theme('invalid_theme')

def test_stylesheet_loading(theme_manager):
    light_style = theme_manager.light_theme
    dark_style = theme_manager.dark_theme
    assert light_style != dark_style
    assert len(light_style) > 0
    assert len(dark_style) > 0