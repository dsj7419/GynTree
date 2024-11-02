# tests/unit/test_ThemeManager.py
import pytest
import logging
import gc
import psutil
from typing import Optional

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt
from utilities.theme_manager import ThemeManager

pytestmark = pytest.mark.unit

logger = logging.getLogger(__name__)

class ThemeTestHelper:
    """Helper class for theme testing"""
    def __init__(self):
        self.initial_memory = None
        self.widgets = []

    def create_test_widget(self) -> QWidget:
        """Create a test widget and track it"""
        widget = QWidget()
        self.widgets.append(widget)
        return widget

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

    def cleanup(self) -> None:
        """Clean up created widgets"""
        for widget in self.widgets:
            widget.close()
            widget.deleteLater()
        self.widgets.clear()
        gc.collect()

@pytest.fixture
def helper():
    """Create test helper instance"""
    helper = ThemeTestHelper()
    yield helper
    helper.cleanup()

@pytest.fixture(scope="module")
def app():
    """Create QApplication instance"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.processEvents()

@pytest.fixture
def theme_manager():
    """Create ThemeManager instance"""
    manager = ThemeManager.getInstance()
    initial_theme = manager.get_current_theme()
    yield manager
    manager.set_theme(initial_theme)  # Reset to initial state

@pytest.mark.timeout(30)
def test_singleton_instance(theme_manager, helper):
    """Test singleton pattern implementation"""
    helper.track_memory()
    
    assert ThemeManager.getInstance() is theme_manager
    
    helper.check_memory_usage("singleton test")

@pytest.mark.timeout(30)
def test_initial_theme(theme_manager, helper):
    """Test initial theme state"""
    helper.track_memory()
    
    assert theme_manager.get_current_theme() in ['light', 'dark']
    
    helper.check_memory_usage("initial theme")

@pytest.mark.timeout(30)
def test_set_theme(theme_manager, helper):
    """Test theme setting functionality"""
    helper.track_memory()
    
    initial_theme = theme_manager.get_current_theme()
    new_theme = 'dark' if initial_theme == 'light' else 'light'
    
    theme_manager.set_theme(new_theme)
    assert theme_manager.get_current_theme() == new_theme
    
    helper.check_memory_usage("set theme")

@pytest.mark.timeout(30)
def test_toggle_theme(theme_manager, helper):
    """Test theme toggling functionality"""
    helper.track_memory()
    
    initial_theme = theme_manager.get_current_theme()
    toggled_theme = theme_manager.toggle_theme()
    
    assert toggled_theme != initial_theme
    assert theme_manager.get_current_theme() == toggled_theme
    
    helper.check_memory_usage("toggle theme")

@pytest.mark.timeout(30)
def test_apply_theme(theme_manager, app, helper):
    """Test theme application to widget"""
    helper.track_memory()
    
    test_widget = helper.create_test_widget()
    initial_style = test_widget.styleSheet()
    
    theme_manager.apply_theme(test_widget)
    
    assert test_widget.styleSheet() != initial_style
    
    helper.check_memory_usage("apply theme")

@pytest.mark.timeout(30)
def test_apply_theme_to_all_windows(theme_manager, app, helper):
    """Test theme application to multiple windows"""
    helper.track_memory()
    
    test_widget1 = helper.create_test_widget()
    test_widget2 = helper.create_test_widget()
    
    test_widget1.show()
    test_widget2.show()
    
    initial_style1 = test_widget1.styleSheet()
    initial_style2 = test_widget2.styleSheet()
    
    theme_manager.apply_theme_to_all_windows(app)
    app.processEvents()
    
    assert test_widget1.styleSheet() != initial_style1
    assert test_widget2.styleSheet() != initial_style2
    
    helper.check_memory_usage("apply to all")

@pytest.mark.timeout(30)
def test_theme_changed_signal(theme_manager, qtbot, helper):
    """Test theme change signal emission"""
    helper.track_memory()
    
    with qtbot.waitSignal(theme_manager.themeChanged, timeout=1000) as blocker:
        theme_manager.toggle_theme()
    
    assert blocker.signal_triggered
    
    helper.check_memory_usage("theme signal")

@pytest.mark.timeout(30)
def test_invalid_theme_setting(theme_manager, helper):
    """Test handling of invalid theme setting"""
    helper.track_memory()
    
    with pytest.raises(ValueError):
        theme_manager.set_theme('invalid_theme')
    
    helper.check_memory_usage("invalid theme")

@pytest.mark.timeout(30)
def test_stylesheet_loading(theme_manager, helper):
    """Test stylesheet loading and validity"""
    helper.track_memory()
    
    light_style = theme_manager.light_theme
    dark_style = theme_manager.dark_theme
    
    assert light_style != dark_style
    assert len(light_style) > 0
    assert len(dark_style) > 0
    
    helper.check_memory_usage("stylesheet loading")

@pytest.mark.timeout(30)
def test_theme_persistence(theme_manager, helper):
    """Test theme persistence across instances"""
    helper.track_memory()
    
    initial_theme = theme_manager.get_current_theme()
    new_theme = 'dark' if initial_theme == 'light' else 'light'
    
    theme_manager.set_theme(new_theme)
    
    new_instance = ThemeManager.getInstance()
    assert new_instance.get_current_theme() == new_theme
    
    helper.check_memory_usage("theme persistence")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])