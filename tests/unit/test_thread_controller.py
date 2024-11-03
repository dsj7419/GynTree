import gc
import threading
import time
from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent, Qt, QThread, QThreadPool
from PyQt5.QtTest import QSignalSpy

from controllers.AutoExcludeWorker import AutoExcludeWorker
from controllers.ThreadController import (
    AutoExcludeWorkerRunnable,
    ThreadController,
    WorkerSignals,
)


def process_events():
    """Helper function to process Qt events with delay"""
    for _ in range(3):
        QCoreApplication.processEvents()
        QThread.msleep(10)


@pytest.fixture
def mock_project_context():
    mock = Mock()
    mock.trigger_auto_exclude.return_value = ["test_exclude"]
    return mock


@pytest.fixture
def thread_controller(qapp):
    controller = ThreadController()
    QThreadPool.globalInstance().setMaxThreadCount(4)
    yield controller
    controller.cleanup_thread()
    process_events()
    QThreadPool.globalInstance().waitForDone(1000)
    process_events()


def test_initialization(thread_controller):
    assert isinstance(thread_controller.threadpool, QThreadPool)
    assert thread_controller.active_workers == []


@pytest.mark.timeout(5)
def test_auto_exclude_thread(thread_controller, mock_project_context, qtbot):
    spy = QSignalSpy(thread_controller.worker_finished)

    worker = thread_controller.start_auto_exclude_thread(mock_project_context)
    assert worker is not None
    assert len(thread_controller.active_workers) == 1

    def check_spy():
        process_events()
        return len(spy) > 0

    qtbot.waitUntil(check_spy, timeout=2000)
    process_events()
    assert spy[0][0] == ["test_exclude"]
    assert len(thread_controller.active_workers) == 0


@pytest.mark.timeout(5)
def test_multiple_threads(thread_controller, mock_project_context, qtbot):
    finished_spy = QSignalSpy(thread_controller.worker_finished)

    process_events()
    for _ in range(3):
        worker = thread_controller.start_auto_exclude_thread(mock_project_context)
        assert worker is not None
        process_events()

    def check_signals():
        process_events()
        return len(finished_spy) >= 3

    qtbot.waitUntil(check_signals, timeout=2000)
    process_events()
    assert len(finished_spy) == 3
    assert len(thread_controller.active_workers) == 0


@pytest.mark.timeout(5)
def test_cleanup_thread(thread_controller, mock_project_context, qtbot):
    worker = thread_controller.start_auto_exclude_thread(mock_project_context)
    assert worker is not None
    process_events()

    thread_controller.cleanup_thread()
    process_events()

    assert len(thread_controller.active_workers) == 0


@pytest.mark.timeout(5)
def test_thread_cleanup_during_execution(
    thread_controller, mock_project_context, qtbot
):
    for _ in range(3):
        thread_controller.start_auto_exclude_thread(mock_project_context)
        process_events()

    thread_controller.cleanup_thread()
    process_events()

    assert len(thread_controller.active_workers) == 0


def test_threadpool_management(thread_controller):
    assert thread_controller.threadpool.maxThreadCount() > 0


@pytest.mark.timeout(5)
def test_memory_cleanup(thread_controller, mock_project_context, qtbot):
    worker = thread_controller.start_auto_exclude_thread(mock_project_context)
    assert worker is not None

    def check_workers():
        process_events()
        return len(thread_controller.active_workers) == 0

    qtbot.waitUntil(check_workers, timeout=2000)
    gc.collect()


@pytest.mark.timeout(5)
def test_concurrent_cleanup(thread_controller, mock_project_context, qtbot):
    for _ in range(3):
        thread_controller.start_auto_exclude_thread(mock_project_context)
        process_events()

    thread_controller.cleanup_thread()
    process_events()
    thread_controller.cleanup_thread()
    process_events()

    assert len(thread_controller.active_workers) == 0


@pytest.mark.timeout(5)
def test_signal_connections(thread_controller, mock_project_context, qtbot):
    worker = thread_controller.start_auto_exclude_thread(mock_project_context)
    assert worker is not None
    assert worker in thread_controller.active_workers

    spy = QSignalSpy(thread_controller.worker_finished)

    def check_spy():
        process_events()
        return len(spy) > 0

    qtbot.waitUntil(check_spy, timeout=2000)
    process_events()
    assert worker not in thread_controller.active_workers


def test_worker_signals():
    signals = WorkerSignals()
    assert hasattr(signals, "finished")
    assert hasattr(signals, "error")


@pytest.mark.timeout(5)
def test_worker_runnable(mock_project_context, qtbot):
    worker = AutoExcludeWorkerRunnable(mock_project_context)

    finished_spy = QSignalSpy(worker.signals.finished)
    error_spy = QSignalSpy(worker.signals.error)

    worker.run()

    def check_spy():
        process_events()
        return len(finished_spy) > 0

    qtbot.waitUntil(check_spy, timeout=2000)
    assert len(error_spy) == 0
    assert finished_spy[0][0] == ["test_exclude"]


@pytest.mark.timeout(5)
def test_worker_state(mock_project_context, qtbot):
    worker = AutoExcludeWorkerRunnable(mock_project_context)
    assert not worker._is_running
    assert hasattr(worker, "worker")
    assert isinstance(worker.worker, AutoExcludeWorker)

    worker.run()
    process_events()

    assert not worker._is_running


@pytest.mark.timeout(5)
def test_worker_error_handling(mock_project_context, qtbot):
    mock_project_context.trigger_auto_exclude.side_effect = Exception("Test error")
    worker = AutoExcludeWorkerRunnable(mock_project_context)

    error_spy = QSignalSpy(worker.signals.error)
    finished_spy = QSignalSpy(worker.signals.finished)

    worker.run()

    def check_spy():
        process_events()
        return len(error_spy) > 0

    qtbot.waitUntil(check_spy, timeout=2000)
    assert error_spy[0][0] == "Error in auto-exclusion analysis: Test error"
    assert len(finished_spy) == 0
    assert not worker._is_running


def test_null_project_context(thread_controller):
    worker = thread_controller.start_auto_exclude_thread(None)
    assert worker is None
    assert len(thread_controller.active_workers) == 0


@pytest.mark.timeout(5)
def test_destructor(thread_controller, qapp):
    thread_controller.__del__()
    process_events()
    QThreadPool.globalInstance().waitForDone(1000)
    process_events()
    assert len(thread_controller.active_workers) == 0


@pytest.mark.timeout(5)
def test_thread_error_handling(thread_controller, mock_project_context, qtbot):
    mock_project_context.trigger_auto_exclude.side_effect = RuntimeError(
        "Test runtime error"
    )
    error_spy = QSignalSpy(thread_controller.worker_error)

    worker = thread_controller.start_auto_exclude_thread(mock_project_context)
    assert worker is not None

    def check_error():
        process_events()
        return len(error_spy) > 0

    qtbot.waitUntil(check_error, timeout=2000)
    assert error_spy[0][0] == "Error in auto-exclusion analysis: Test runtime error"


@pytest.mark.timeout(5)
def test_max_threads_handling(thread_controller, mock_project_context, qtbot):
    thread_controller.threadpool.setMaxThreadCount(2)
    workers = []

    for _ in range(4):  # Try to start more threads than max
        worker = thread_controller.start_auto_exclude_thread(mock_project_context)
        assert worker is not None
        workers.append(worker)
        process_events()

    # Verify queuing behavior
    assert thread_controller.threadpool.activeThreadCount() <= 2

    # Wait for completion
    QThreadPool.globalInstance().waitForDone()
    process_events()
    assert len(thread_controller.active_workers) == 0


@pytest.mark.timeout(5)
def test_thread_priority(thread_controller, mock_project_context, qtbot):
    worker = thread_controller.start_auto_exclude_thread(mock_project_context)
    assert worker is not None
    assert worker.priority() == QThread.NormalPriority
    process_events()


@pytest.mark.timeout(5)
def test_mutex_protection(thread_controller, mock_project_context, qtbot):
    finished_spy = QSignalSpy(thread_controller.worker_finished)

    # Start multiple threads rapidly
    workers = []
    for _ in range(10):
        worker = thread_controller.start_auto_exclude_thread(mock_project_context)
        assert worker is not None
        workers.append(worker)
        process_events()

    def check_completion():
        process_events()
        return len(finished_spy) >= 10

    qtbot.waitUntil(check_completion, timeout=5000)
    process_events()
    assert len(finished_spy) == 10
    assert len(thread_controller.active_workers) == 0


@pytest.mark.timeout(5)
def test_cleanup_during_error(thread_controller, mock_project_context, qtbot):
    mock_project_context.trigger_auto_exclude.side_effect = Exception(
        "Cleanup test error"
    )
    worker = thread_controller.start_auto_exclude_thread(mock_project_context)
    assert worker is not None

    error_spy = QSignalSpy(thread_controller.worker_error)

    def check_error():
        process_events()
        return len(error_spy) > 0

    qtbot.waitUntil(check_error, timeout=2000)
    assert len(thread_controller.active_workers) == 0
