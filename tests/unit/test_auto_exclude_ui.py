# tests/unit/test_auto_exclude_ui.py
import pytest
from PyQt5.QtWidgets import (
    QMainWindow, QTreeWidgetItem, QMessageBox, QApplication,
    QPushButton, QLabel
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QFont, QCloseEvent
from components.UI.AutoExcludeUI import AutoExcludeUI
from utilities.theme_manager import ThemeManager

pytestmark = pytest.mark.unit

@pytest.fixture
def mock_managers(mocker, setup_theme_files):
    """Create mock managers for testing"""
    auto_exclude_manager = mocker.Mock()
    settings_manager = mocker.Mock()
    theme_manager = mocker.Mock()
    theme_manager.apply_theme = mocker.Mock()
    project_context = mocker.Mock()
    
    # Setup mock returns
    exclusions = {
        'root_exclusions': {'node_modules', '.git'},
        'excluded_dirs': {'dist', 'build'},
        'excluded_files': {'.env', 'package-lock.json'}
    }
    
    # Configure auto_exclude_manager mock
    auto_exclude_manager.get_recommendations.return_value = exclusions
    
    # Configure settings_manager mock
    settings_manager.get_all_exclusions.return_value = exclusions
    
    # Configure project_context mock's settings_manager
    project_context.settings_manager = mocker.Mock()
    project_context.settings_manager.get_root_exclusions.return_value = exclusions['root_exclusions']
    project_context.settings_manager.get_excluded_dirs.return_value = exclusions['excluded_dirs']
    project_context.settings_manager.get_excluded_files.return_value = exclusions['excluded_files']
    
    return {
        'auto_exclude': auto_exclude_manager,
        'settings': settings_manager,
        'theme': theme_manager,
        'context': project_context
    }

@pytest.fixture
def auto_exclude_ui(qtbot, mock_managers):
    """Create AutoExcludeUI instance"""
    ui = AutoExcludeUI(
        mock_managers['auto_exclude'],
        mock_managers['settings'],
        ["Recommendation 1", "Recommendation 2"],
        mock_managers['context'],
        theme_manager=mock_managers['theme'],
        apply_initial_theme=False
    )
    qtbot.addWidget(ui)
    ui.show()
    return ui

def test_initialization(auto_exclude_ui):
    """Test initial UI setup"""
    assert isinstance(auto_exclude_ui, QMainWindow)
    assert auto_exclude_ui.windowTitle() == 'Auto-Exclude Recommendations'
    assert auto_exclude_ui.tree_widget is not None

def test_ui_components(auto_exclude_ui):
    """Test presence and properties of UI components"""
    # Test title label
    title_label = auto_exclude_ui.findChild(QLabel)
    assert title_label is not None
    assert title_label.font().pointSize() == 16
    assert title_label.font().weight() == QFont.Bold

    # Test buttons
    collapse_btn = auto_exclude_ui.findChild(QPushButton, "collapse_btn")
    expand_btn = auto_exclude_ui.findChild(QPushButton, "expand_btn")
    apply_btn = auto_exclude_ui.findChild(QPushButton, "apply_button")
    
    assert collapse_btn is not None
    assert expand_btn is not None
    assert apply_btn is not None

def test_tree_widget_setup(auto_exclude_ui):
    """Test tree widget configuration"""
    tree = auto_exclude_ui.tree_widget
    assert tree.columnCount() == 2
    assert tree.headerItem().text(0) == 'Name'
    assert tree.headerItem().text(1) == 'Type'

@pytest.mark.timeout(30)
def test_populate_tree(auto_exclude_ui, qtbot):
    """Test tree population with exclusions"""
    auto_exclude_ui.populate_tree()
    
    root = auto_exclude_ui.tree_widget.invisibleRootItem()
    assert root.childCount() > 0
    
    # Verify category items
    categories = ['Root Exclusions', 'Excluded Dirs', 'Excluded Files']
    for i in range(root.childCount()):
        category = root.child(i)
        assert category.text(0) in categories

@pytest.mark.timeout(30)
def test_combined_exclusions(auto_exclude_ui, mock_managers):
    """Test getting combined exclusions"""
    combined = auto_exclude_ui.get_combined_exclusions()
    
    assert 'root_exclusions' in combined
    assert 'excluded_dirs' in combined
    assert 'excluded_files' in combined
    
    assert 'node_modules' in combined['root_exclusions']
    assert 'dist' in combined['excluded_dirs']
    assert '.env' in combined['excluded_files']

@pytest.mark.timeout(30)
def test_apply_exclusions(auto_exclude_ui, mock_managers, qtbot, mocker):
    """Test applying exclusions"""
    mock_message_box = mocker.patch.object(QMessageBox, 'information')
    mock_close = mocker.patch.object(auto_exclude_ui, 'close')
    
    auto_exclude_ui.apply_exclusions()
    
    mock_managers['auto_exclude'].apply_recommendations.assert_called_once()
    mock_message_box.assert_called_once()
    mock_close.assert_called_once()

@pytest.mark.timeout(30)
def test_update_recommendations(auto_exclude_ui, qtbot):
    """Test updating recommendations"""
    new_recommendations = ["New Recommendation 1", "New Recommendation 2"]
    
    auto_exclude_ui.update_recommendations(new_recommendations)
    
    root = auto_exclude_ui.tree_widget.invisibleRootItem()
    assert root.childCount() > 0

@pytest.mark.timeout(30)
def test_theme_application(auto_exclude_ui, mock_managers):
    """Test theme application"""
    mock_theme_apply = mock_managers['theme'].apply_theme
    mock_theme_apply.reset_mock()
    
    auto_exclude_ui.apply_theme()
    mock_theme_apply.assert_called_once_with(auto_exclude_ui)

@pytest.fixture
def cleanup_ui():
    """Fixture to clean up UI objects after tests"""
    uis = []
    yield uis
    for ui in uis:
        if ui is not None:
            try:
                ui.close()
                ui.deleteLater()
            except (RuntimeError, AttributeError):
                pass

@pytest.mark.timeout(30)
def test_theme_manager_initialization(qtbot, mock_managers, mocker):
    """Test theme manager initialization with and without explicit theme manager"""
    # Set up mock for ThemeManager.getInstance()
    mock_theme_manager = mocker.Mock()
    mocker.patch('components.UI.AutoExcludeUI.ThemeManager.getInstance',
                 return_value=mock_theme_manager)
    
    # Test with explicit theme manager
    ui = AutoExcludeUI(
        mock_managers['auto_exclude'],
        mock_managers['settings'],
        ["Recommendation 1", "Recommendation 2"],
        mock_managers['context'],
        theme_manager=mock_managers['theme'],
        apply_initial_theme=False
    )
    assert ui.theme_manager == mock_managers['theme']
    
    # Test with default theme manager
    ui2 = AutoExcludeUI(
        mock_managers['auto_exclude'],
        mock_managers['settings'],
        ["Recommendation 1", "Recommendation 2"],
        mock_managers['context'],
        apply_initial_theme=False
    )
    # Should get the mock from getInstance()
    assert ui2.theme_manager == mock_theme_manager
    
    # Cleanup
    ui.close()
    ui.deleteLater()
    ui2.close()
    ui2.deleteLater()

@pytest.mark.timeout(30)
def test_theme_change_signal(qtbot, mock_managers):
    """Test theme change signal connection"""
    ui = AutoExcludeUI(
        mock_managers['auto_exclude'],
        mock_managers['settings'],
        ["Recommendation 1", "Recommendation 2"],
        mock_managers['context'],
        theme_manager=mock_managers['theme'],
        apply_initial_theme=False
    )
    
    # Verify theme change signal connection
    mock_managers['theme'].themeChanged.connect.assert_called_once()
    assert mock_managers['theme'].themeChanged.connect.call_args[0][0] == ui.apply_theme

@pytest.mark.timeout(30)
def test_expand_collapse_buttons(auto_exclude_ui, qtbot):
    """Test expand/collapse functionality"""
    collapse_btn = auto_exclude_ui.findChild(QPushButton, "collapse_btn")
    expand_btn = auto_exclude_ui.findChild(QPushButton, "expand_btn")
    
    assert collapse_btn is not None, "Collapse button not found"
    assert expand_btn is not None, "Expand button not found"
    
    # Test collapse with error checking
    try:
        QTest.mouseClick(collapse_btn, Qt.LeftButton)
        qtbot.wait(100)
    except Exception as e:
        pytest.fail(f"Failed to click collapse button: {str(e)}")
    
    # Verify all items are collapsed
    root = auto_exclude_ui.tree_widget.invisibleRootItem()
    assert root is not None, "Root item not found"
    for i in range(root.childCount()):
        assert not root.child(i).isExpanded()
    
    # Test expand with error checking
    try:
        QTest.mouseClick(expand_btn, Qt.LeftButton)
        qtbot.wait(100)
    except Exception as e:
        pytest.fail(f"Failed to click expand button: {str(e)}")
    
    # Verify all items are expanded
    for i in range(root.childCount()):
        assert root.child(i).isExpanded()

@pytest.mark.timeout(30)
def test_window_close(auto_exclude_ui, qtbot, mocker):
    """Test window close behavior"""
    close_event = QCloseEvent()
    spy = mocker.spy(close_event, 'ignore') 
    auto_exclude_ui.closeEvent(close_event)
    assert not spy.called

def test_tree_item_flags(auto_exclude_ui):
    """Test tree item flags configuration"""
    root = auto_exclude_ui.tree_widget.invisibleRootItem()
    for i in range(root.childCount()):
        category = root.child(i)
        if category.text(0) != 'Root Exclusions':
            for j in range(category.childCount()):
                item = category.child(j)
                assert item.flags() & Qt.ItemIsUserCheckable

@pytest.mark.timeout(30)
def test_memory_management(auto_exclude_ui, qtbot):
    """Test memory management during updates"""
    import gc
    import psutil
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Perform multiple updates
    for _ in range(10):
        auto_exclude_ui.populate_tree()
        qtbot.wait(100)
        gc.collect()
    
    final_memory = process.memory_info().rss
    memory_diff = final_memory - initial_memory
    
    # Check for memory leaks (less than 10MB increase)
    assert memory_diff < 10 * 1024 * 1024

def test_window_geometry(auto_exclude_ui):
    """Test window geometry settings"""
    geometry = auto_exclude_ui.geometry()
    assert geometry.width() == 800
    assert geometry.height() == 600
    assert geometry.x() == 300
    assert geometry.y() == 150

@pytest.mark.timeout(30)
def test_rapid_updates(auto_exclude_ui, qtbot):
    """Test UI stability during rapid updates"""
    recommendations = ["Recommendation 1", "Recommendation 2"]
    
    # Perform rapid updates
    for _ in range(10):
        auto_exclude_ui.update_recommendations(recommendations)
        qtbot.wait(50)
    
    assert auto_exclude_ui.tree_widget.topLevelItemCount() > 0

def test_error_handling(auto_exclude_ui, mock_managers, mocker):
    """Test error handling in UI operations"""
    mock_managers['auto_exclude'].apply_recommendations.side_effect = Exception("Test error")
    mock_message_box = mocker.patch.object(QMessageBox, 'critical')
    
    auto_exclude_ui.apply_exclusions()
    mock_message_box.assert_called_once()