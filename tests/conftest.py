import queue
import shutil
import sys
import os
import pytest
import threading
from PyQt5.QtWidgets import QApplication
import psutil
from typing import Optional, List, Dict, Any
from PyQt5.QtCore import Qt, QTimer, QEventLoop
from PyQt5.QtTest import QTest
import logging
import logging.handlers
import gc
from pathlib import Path
import weakref
import tempfile
import atexit
from contextlib import contextmanager, ExitStack
import time
from queue import Queue

# Add src directory to path for compatibility
SRC_PATH = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(SRC_PATH))

from models.Project import Project
from services.SettingsManager import SettingsManager
from services.ProjectTypeDetector import ProjectTypeDetector
from services.ProjectContext import ProjectContext
from utilities.theme_manager import ThemeManager

# Configure logging with thread-safe implementation
LOG_DIR = Path('tests/reports/logs')
LOG_DIR.mkdir(parents=True, exist_ok=True)

class ThreadSafeLogQueue:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ThreadSafeLogQueue, cls).__new__(cls)
                cls._instance.queue = queue.Queue()
                cls._instance.handler = None
                cls._instance.listener = None
                cls._instance.initialize_handler()
            return cls._instance
    
    def _create_stream_handler(self):
        """Create and configure stream handler"""
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        return handler
    
    def _create_file_handler(self):
        """Create and configure file handler"""
        log_file = LOG_DIR / 'pytest_execution.log'
        handler = logging.FileHandler(log_file, 'w', 'utf-8', delay=True)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        return handler
    
    def initialize_handler(self):
        if self.handler is None:
            self.handler = logging.handlers.QueueHandler(self.queue)
            stream_handler = self._create_stream_handler()
            file_handler = self._create_file_handler()
            self.listener = logging.handlers.QueueListener(
                self.queue,
                stream_handler,
                file_handler,
                respect_handler_level=True
            )
            self.listener.start()
    
    def cleanup(self):
        """Enhanced cleanup with proper lock handling and shutdown coordination"""
        with self._lock:
            if hasattr(self, 'listener') and self.listener:
                try:
                    # Flush any remaining messages
                    while not self.queue.empty():
                        try:
                            self.queue.get_nowait()
                        except queue.Empty:
                            break
                    
                    # Stop the listener before clearing
                    self.listener.stop()
                    self.queue.queue.clear()
                    
                    # Remove handler references
                    root_logger = logging.getLogger()
                    if self.handler in root_logger.handlers:
                        root_logger.removeHandler(self.handler)
                    
                    self.listener = None
                    self.handler = None
                except Exception as e:
                    print(f"Non-critical logger cleanup warning: {e}")

# Initialize thread-safe logging
log_queue = ThreadSafeLogQueue()
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[log_queue.handler]
)
logger = logging.getLogger(__name__)

def mock_msg_box(*args, **kwargs):
    """Mock function for QMessageBox to prevent dialogs from blocking tests"""
    return 0  # Simulates clicking "OK"

# Global timeout settings
TEST_TIMEOUT = 30  # seconds
CLEANUP_TIMEOUT = 5  # seconds
QT_WAIT_TIMEOUT = 100  # milliseconds

# Enhanced test artifacts management
class TestArtifacts:
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix='gyntree_test_'))
        self.threads: List[threading.Thread] = []
        self.qt_widgets: List[weakref.ref] = []
        self.processes: List[psutil.Process] = []
        self._cleanup_queue = Queue()
        self._widget_refs = set()

    def track_widget(self, widget):
        """Track a Qt widget for cleanup with reference management"""
        if widget and not any(ref() is widget for ref in self.qt_widgets):
            ref = weakref.ref(widget, self._widget_finalizer)
            self.qt_widgets.append(ref)
            self._widget_refs.add(ref)
            logger.debug(f"Tracking widget: {widget.__class__.__name__}")

    def _widget_finalizer(self, ref):
        """Callback when widget is garbage collected"""
        if ref in self._widget_refs:
            self._widget_refs.remove(ref)
        self.qt_widgets = [w for w in self.qt_widgets if w() is not None]

    def cleanup(self):
        """Enhanced full cleanup for all test artifacts"""
        # Stop logging before cleanup to prevent log-during-cleanup issues
        log_queue.cleanup()
        
        try:
            print("Starting test artifacts cleanup")  # Use print instead of logging
            self._cleanup_threads()
            self._cleanup_qt_widgets()
            self._cleanup_processes()
            self._cleanup_temp_dir()
        except Exception as e:
            print(f"Non-critical cleanup warning: {str(e)}")
        finally:
            print("Test artifacts cleanup completed")

    def _cleanup_threads(self):
        """Enhanced thread cleanup"""
        current_thread = threading.current_thread()
        for thread in self.threads[:]:
            if thread is not current_thread and thread.is_alive():
                try:
                    thread.join(timeout=CLEANUP_TIMEOUT)
                except Exception:
                    logger.warning(f"Thread {thread.name} cleanup failed")
                finally:
                    self.threads.remove(thread)

    def _cleanup_qt_widgets(self):
        """Enhanced Qt widget cleanup with error handling"""
        app = QApplication.instance()
        if not app:
            return

        app.processEvents()
        remaining = []
        
        for widget_ref in self.qt_widgets[:]:
            widget = widget_ref()
            if widget:
                try:
                    if hasattr(widget, 'cleanup'):
                        widget.cleanup()
                    if not widget.isHidden():
                        widget.close()
                    widget.deleteLater()
                    app.processEvents()
                    QTest.qWait(10)
                except RuntimeError:
                    # Widget already deleted
                    pass
                except Exception as e:
                    logger.warning(f"Widget cleanup error: {e}")
                    remaining.append(widget_ref)

        self.qt_widgets = [ref for ref in remaining if ref() is not None]
        
        # Final cleanup
        for _ in range(3):
            app.processEvents()
            QTest.qWait(QT_WAIT_TIMEOUT)
            gc.collect()

    def _cleanup_processes(self):
        """Enhanced process cleanup"""
        for proc in self.processes[:]:
            try:
                if proc.is_running():
                    proc.terminate()
                    proc.wait(timeout=CLEANUP_TIMEOUT)
            except psutil.TimeoutExpired:
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass
            except Exception as e:
                logger.warning(f"Process cleanup error: {e}")
            finally:
                self.processes.remove(proc)

    def _cleanup_temp_dir(self):
        """Enhanced temporary directory cleanup"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Temp directory cleanup error: {e}")

# Global instance for managing test artifacts
test_artifacts = TestArtifacts()
atexit.register(test_artifacts.cleanup)

@contextmanager
def qt_wait_signal(signal, timeout=1000):
    """Wait for Qt signal with a timeout"""
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    signal.connect(loop.quit)
    timer.timeout.connect(loop.quit)
    timer.start(timeout)
    loop.exec_()
    if timer.isActive():
        timer.stop()
        return True
    else:
        raise TimeoutError("Signal wait timed out")

@pytest.fixture(scope="session")
def qapp():
    """Provide a QApplication instance for test session"""
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    app.setAttribute(Qt.AA_DontUseNativeDialogs)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    yield app
    app.quit()

@pytest.fixture
def qtbot_timeout(qtbot):
    """QtBot fixture with timeout for condition checking"""
    def wait_until(func, timeout=5000, interval=50):
        deadline = time.time() + (timeout / 1000)
        while time.time() < deadline:
            if func():
                return True
            qtbot.wait(interval)
        raise TimeoutError(f"Condition not met within {timeout}ms")
    qtbot.wait_until = wait_until
    yield qtbot

@contextmanager
def logger_context():
    """Context manager for managing logging in tests"""
    queue_handler = logging.handlers.QueueHandler(queue.Queue())
    loggers = [
        logging.getLogger('test_execution'),
        logging.getLogger('conftest'),
        logging.getLogger('controllers.AppController'),
        logging.getLogger('controllers.ThreadController'),
        logging.getLogger('components.UI.DashboardUI'),
        logging.getLogger('utilities.logging_decorator')
    ]
    handlers = []
    try:
        for logger in loggers:
            handler = logging.NullHandler()
            logger.addHandler(handler)
            logger.addHandler(queue_handler)
            handlers.append((logger, handler))
        test_logger = logging.getLogger('test_execution')
        yield test_logger
    finally:
        for logger, handler in reversed(handlers):
            logger.removeHandler(handler)
            logger.removeHandler(queue_handler)
        app = QApplication.instance()
        if app:
            app.processEvents()

@contextmanager
def coordinated_qt_cleanup(qt_test_helper, test_artifacts):
    """Coordinate cleanup between Qt test helper and test artifacts"""
    try:
        yield
    finally:
        QApplication.processEvents()
        qt_test_helper.cleanup()
        QApplication.processEvents()
        QTest.qWait(QT_WAIT_TIMEOUT)
        test_artifacts._cleanup_qt_widgets()
        QApplication.processEvents()
        gc.collect()

@pytest.fixture(autouse=True)
def cleanup_threads():
    """Auto-cleanup remaining threads after each test"""
    yield
    test_artifacts._cleanup_threads()

@pytest.fixture(autouse=True)
def cleanup_processes():
    """Auto-cleanup remaining processes after each test"""
    yield
    test_artifacts._cleanup_processes()

@pytest.fixture
def mock_project(tmp_path):
    """Provide a mock Project instance for tests"""
    return Project(
        name="test_project",
        start_directory=str(tmp_path),
        root_exclusions=["node_modules"],
        excluded_dirs=["dist"],
        excluded_files=[".env"]
    )

@pytest.fixture
def settings_manager(mock_project, tmp_path):
    """Provide a SettingsManager instance for tests"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    SettingsManager.config_dir = str(config_dir)
    return SettingsManager(mock_project)

@pytest.fixture
def project_type_detector(tmp_path):
    """Provide a ProjectTypeDetector instance for tests"""
    return ProjectTypeDetector(str(tmp_path))

@pytest.fixture
def project_context(mock_project):
    """Provide a ProjectContext instance for tests"""
    context = ProjectContext(mock_project)
    yield context
    context.close()
    gc.collect()

@pytest.fixture
def theme_manager():
    """Provide a ThemeManager instance for tests"""
    manager = ThemeManager.getInstance()
    original_theme = manager.get_current_theme()
    yield manager
    manager.set_theme(original_theme)
    gc.collect()

def pytest_addoption(parser):
    """Add custom command-line options"""
    parser.addoption("--qt-wait", action="store", default=QT_WAIT_TIMEOUT, type=int)
    parser.addoption("--cleanup-timeout", action="store", default=CLEANUP_TIMEOUT, type=int)
    parser.addoption("--test-artifacts-dir", action="store", default=None)

def pytest_configure(config):
    """Add custom markers to pytest configuration"""
    config.addinivalue_line("markers", "unit: marks unit tests")
    config.addinivalue_line("markers", "integration: marks integration tests")
    config.addinivalue_line("markers", "performance: marks performance tests")
    config.addinivalue_line("markers", "gui: marks tests that require GUI")
    config.addinivalue_line("markers", "timeout: marks tests with custom timeout")
    config.addinivalue_line("markers", "cleanup: marks tests with custom cleanup requirements")
    config.addinivalue_line("markers", "windows: marks tests specific to Windows")
    config.addinivalue_line("markers", "slow: marks tests that are expected to be slow-running")
    
    artifacts_dir = config.getoption("--test-artifacts-dir")
    if artifacts_dir:
        test_artifacts.temp_dir = Path(artifacts_dir)
        test_artifacts.temp_dir.mkdir(parents=True, exist_ok=True)

@pytest.fixture(autouse=True)
def _app_context(qapp):
    """Ensure Qt application context is active for each test"""
    try:
        yield
    finally:
        for _ in range(3):
            qapp.processEvents()
            QTest.qWait(QT_WAIT_TIMEOUT)
        gc.collect()

@pytest.fixture(autouse=True)
def _gc_cleanup():
    """Force garbage collection after each test for memory management"""
    yield
    for _ in range(3):
        gc.collect()
        time.sleep(0.1)

def pytest_sessionfinish(session, exitstatus):
    """Finalize and cleanup after test session"""
    app = QApplication.instance()
    if app:
        app.processEvents()
    try:
        # Simplified cleanup without logger context
        print("Cleaning up after test session...")
        test_artifacts.cleanup()
    except Exception as e:
        print(f"Non-critical cleanup warning: {e}")
    finally:
        logging.shutdown()

@pytest.fixture(autouse=True)
def setup_theme_files(tmp_path):
    """Create temporary theme files for testing"""
    # Create theme files in temp directory instead of src
    test_styles_dir = tmp_path / 'styles'
    test_styles_dir.mkdir(parents=True, exist_ok=True)
    
    # Create theme files in temp directory
    light_theme = test_styles_dir / 'light_theme.qss'
    dark_theme = test_styles_dir / 'dark_theme.qss'
    
    # Write test theme content
    light_theme.write_text("""
        QMainWindow {
            background-color: #ffffff;
        }
    """)
    dark_theme.write_text("""
        QMainWindow {
            background-color: #333333;
        }
    """)
    
    # Store original resource path function
    original_get_resource_path = None
    
    try:
        # Patch get_resource_path to use our test directory
        from utilities.resource_path import get_resource_path
        original_get_resource_path = get_resource_path
        
        def test_get_resource_path(relative_path):
            if 'styles/' in relative_path:
                return str(test_styles_dir / relative_path.split('/')[-1])
            return original_get_resource_path(relative_path)
            
        import utilities.resource_path
        utilities.resource_path.get_resource_path = test_get_resource_path
        
        # Clear ThemeManager singleton if it exists
        if hasattr(ThemeManager, '_instance') and ThemeManager._instance is not None:
            ThemeManager._instance = None
        
        yield
        
    finally:
        # Restore original get_resource_path function
        if original_get_resource_path:
            utilities.resource_path.get_resource_path = original_get_resource_path
            
        # Reset ThemeManager singleton
        if hasattr(ThemeManager, '_instance'):
            ThemeManager._instance = None