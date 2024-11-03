import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt5.QtCore import QCoreApplication, Qt, QThread, QTimer
from PyQt5.QtTest import QSignalSpy
from PyQt5.QtWidgets import QApplication

from controllers.AutoExcludeWorker import AutoExcludeWorker
from controllers.ThreadController import AutoExcludeWorkerRunnable, ThreadController
from models.Project import Project
from services.DirectoryAnalyzer import DirectoryAnalyzer
from services.ProjectContext import ProjectContext


@pytest.fixture
def app():
    return QApplication([])


@pytest.fixture
def thread_controller():
    controller = ThreadController()
    yield controller
    controller.cleanup_thread()


class TestConcurrency:
    def test_thread_controller_multiple_workers(self, thread_controller):
        mock_context = Mock()
        workers = []

        # Start multiple workers
        for _ in range(3):
            worker = thread_controller.start_auto_exclude_thread(mock_context)
            workers.append(worker)

        assert len(thread_controller.active_workers) == 3

        # Test cleanup
        thread_controller.cleanup_thread()
        # Process events to ensure signals are delivered
        QCoreApplication.processEvents()
        time.sleep(0.1)
        QCoreApplication.processEvents()

        assert len(thread_controller.active_workers) == 0

    def test_worker_parallel_execution(self, thread_controller):
        execution_order = []
        execution_lock = threading.Lock()

        def mock_work():
            with execution_lock:
                execution_order.append(threading.current_thread().name)
            time.sleep(0.1)

        mock_context = Mock()
        mock_context.trigger_auto_exclude = mock_work

        # Start multiple workers
        workers = [
            thread_controller.start_auto_exclude_thread(mock_context) for _ in range(3)
        ]

        # Wait for completion and process events
        time.sleep(0.5)
        QCoreApplication.processEvents()

        assert len(execution_order) == 3
        assert len(set(execution_order)) == 3

    def test_directory_analyzer_concurrent_access(self):
        analyzer = DirectoryAnalyzer("/test/path", Mock())
        results = []
        threads = []

        def analyze():
            results.append(analyzer.analyze_directory())

        # Create multiple threads
        for _ in range(3):
            thread = threading.Thread(target=analyze)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        assert len(results) == 3
        assert all(isinstance(r, dict) for r in results)

    def test_worker_state_transitions(self, thread_controller):
        mock_context = Mock()
        worker = thread_controller.start_auto_exclude_thread(mock_context)

        assert not worker._stop_requested

        # Test stop request
        worker.cleanup()
        QCoreApplication.processEvents()

        assert worker._stop_requested
        assert not worker._is_running

    def test_thread_controller_signal_handling(self, thread_controller):
        mock_context = Mock()
        mock_context.trigger_auto_exclude.return_value = ["test recommendation"]

        # Create signal spy
        finished_spy = QSignalSpy(thread_controller.worker_finished)

        worker = thread_controller.start_auto_exclude_thread(mock_context)

        # Wait for signals and process events
        start_time = time.time()
        while len(finished_spy) == 0 and time.time() - start_time < 1.0:
            QCoreApplication.processEvents()
            time.sleep(0.01)

        assert len(finished_spy) > 0
        assert finished_spy[0][0] == ["test recommendation"]

    @patch("pathlib.Path.exists")
    def test_concurrent_project_operations(self, mock_exists):
        # Mock directory existence check
        mock_exists.return_value = True

        # Create a Project instance with mocked directory check
        project = Project("test", "/test/path")

        context = ProjectContext(project)

        def concurrent_operation():
            try:
                context.trigger_auto_exclude()
            except Exception:
                pass

        threads = []
        for _ in range(3):
            thread = threading.Thread(target=concurrent_operation)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert not context._is_active or context.is_initialized

    def test_worker_error_propagation(self, thread_controller):
        mock_context = Mock()
        mock_context.trigger_auto_exclude.side_effect = Exception("Test error")

        error_spy = QSignalSpy(thread_controller.worker_error)

        worker = thread_controller.start_auto_exclude_thread(mock_context)

        # Wait for error signal and process events
        start_time = time.time()
        while len(error_spy) == 0 and time.time() - start_time < 1.0:
            QCoreApplication.processEvents()
            time.sleep(0.01)

        assert len(error_spy) > 0
        assert "Test error" in str(error_spy[0][0])

    def test_thread_pool_management(self, thread_controller):
        initial_thread_count = threading.active_count()
        mock_context = Mock()

        # Start workers up to max thread count
        max_threads = thread_controller.threadpool.maxThreadCount()
        workers = []

        for _ in range(max_threads + 2):
            worker = thread_controller.start_auto_exclude_thread(mock_context)
            workers.append(worker)
            QCoreApplication.processEvents()

        time.sleep(0.1)  # Allow threads to start
        QCoreApplication.processEvents()

        # Verify thread count doesn't exceed maximum
        current_threads = threading.active_count() - initial_thread_count
        assert current_threads <= max_threads

    def test_concurrent_cleanup(self, thread_controller):
        mock_context = Mock()
        workers = []

        # Start workers
        for _ in range(3):
            worker = thread_controller.start_auto_exclude_thread(mock_context)
            workers.append(worker)
            QCoreApplication.processEvents()

        # Initiate cleanup while workers are running
        cleanup_thread = threading.Thread(target=thread_controller.cleanup_thread)
        cleanup_thread.start()

        # Wait for cleanup with timeout and process events
        start_time = time.time()
        while cleanup_thread.is_alive() and time.time() - start_time < 2.0:
            QCoreApplication.processEvents()
            time.sleep(0.01)

        assert not cleanup_thread.is_alive()
        assert len(thread_controller.active_workers) == 0

    def test_thread_priority(self, thread_controller):
        mock_context = Mock()
        worker = thread_controller.start_auto_exclude_thread(mock_context)
        QCoreApplication.processEvents()

        assert worker.priority() == QThread.NormalPriority

        # Test priority change
        worker.setPriority(QThread.HighPriority)
        QCoreApplication.processEvents()

        assert worker.priority() == QThread.HighPriority
