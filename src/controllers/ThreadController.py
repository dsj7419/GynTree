import logging
from typing import List, Optional

from PyQt5.QtCore import (
    QCoreApplication,
    QEvent,
    QMutex,
    QMutexLocker,
    QObject,
    QRunnable,
    Qt,
    QThread,
    QThreadPool,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)

from controllers.AutoExcludeWorker import AutoExcludeWorker
from services.ProjectContext import ProjectContext

logger = logging.getLogger(__name__)


class WorkerFinishedEvent(QEvent):
    EventType = QEvent.Type(QEvent.User + 1)

    def __init__(self, result: List[str]) -> None:
        super().__init__(WorkerFinishedEvent.EventType)
        self.result = result


class WorkerErrorEvent(QEvent):
    EventType = QEvent.Type(QEvent.User + 2)

    def __init__(self, error: str) -> None:
        super().__init__(WorkerErrorEvent.EventType)
        self.error = error


class WorkerSignals(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    cleanup = pyqtSignal()


class AutoExcludeWorkerRunnable(QRunnable):
    def __init__(self, project_context: ProjectContext) -> None:
        super().__init__()
        self.setAutoDelete(True)
        self._priority = QThread.NormalPriority
        if project_context is None:
            raise ValueError("Project context cannot be None")

        self.worker = AutoExcludeWorker(project_context)
        self.signals = WorkerSignals()
        self._is_running = False
        self._stop_requested = False

        self.worker.finished.connect(self._handle_worker_finished)
        self.worker.error.connect(self._handle_worker_error)
        self.signals.cleanup.connect(self.cleanup)

    def cleanup(self) -> None:
        self._stop_requested = True
        self._is_running = False
        self._process_events()

    def priority(self) -> int:
        return self._priority

    def setPriority(self, priority: QThread.Priority) -> None:
        self._priority = priority

    def _handle_worker_finished(self, result: str) -> None:
        if not self._stop_requested:
            self.signals.finished.emit([result])

        self._is_running = False
        QTimer.singleShot(0, self._process_events)

    def _handle_worker_error(self, error: str) -> None:
        if not self._stop_requested:
            self.signals.error.emit(str(error))

        self._is_running = False
        QTimer.singleShot(0, self._process_events)

    def _process_events(self) -> None:
        QCoreApplication.processEvents()

    @pyqtSlot()
    def run(self) -> None:
        if self._is_running or self._stop_requested:
            return

        self._is_running = True
        try:
            self.worker.run()
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in worker runnable: {error_msg}")
            if not self._stop_requested:
                self.signals.error.emit(error_msg)
        finally:
            self._is_running = False
            self._process_events()


class ThreadController(QObject):
    worker_finished = pyqtSignal(list)
    worker_error = pyqtSignal(str)
    cleanup_complete = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.threadpool = QThreadPool()
        self.active_workers: List[AutoExcludeWorkerRunnable] = []
        self._mutex = QMutex(QMutex.RecursionMode.Recursive)
        self.moveToThread(QCoreApplication.instance().thread())  # type: ignore
        QTimer.singleShot(0, self._process_events)
        logger.debug(
            f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads"
        )

    def start_auto_exclude_thread(
        self, project_context: ProjectContext
    ) -> Optional[AutoExcludeWorkerRunnable]:
        if not project_context:
            logger.error("Cannot start thread with None project context")
            return None

        try:
            worker = AutoExcludeWorkerRunnable(project_context)

            def finished_handler(result: List[str]) -> None:
                with QMutexLocker(self._mutex):
                    event = WorkerFinishedEvent(result)
                    app = QCoreApplication.instance()
                    if app:
                        app.postEvent(self, event, Qt.HighEventPriority)
                    QTimer.singleShot(0, self._process_events)

            def error_handler(error: str) -> None:
                with QMutexLocker(self._mutex):
                    event = WorkerErrorEvent(error)
                    app = QCoreApplication.instance()
                    if app:
                        app.postEvent(self, event, Qt.HighEventPriority)
                    QTimer.singleShot(0, self._process_events)

            worker.signals.finished.connect(finished_handler)
            worker.signals.error.connect(error_handler)

            with QMutexLocker(self._mutex):
                self.active_workers.append(worker)
                self.threadpool.start(worker)
                QTimer.singleShot(0, self._process_events)

            return worker

        except Exception as e:
            logger.error(f"Error creating worker: {str(e)}")
            return None

    def _process_events(self) -> None:
        app = QCoreApplication.instance()
        if app and QThread.currentThread() == app.thread():
            app.processEvents()

    def event(self, event: QEvent) -> bool:
        if event.type() == WorkerFinishedEvent.EventType:
            if isinstance(event, WorkerFinishedEvent):
                self._handle_worker_finished(event)
                return True
        elif event.type() == WorkerErrorEvent.EventType:
            if isinstance(event, WorkerErrorEvent):
                self._handle_worker_error(event)
                return True
        return super().event(event)

    def _handle_worker_finished(self, event: WorkerFinishedEvent) -> None:
        with QMutexLocker(self._mutex):
            try:
                self.worker_finished.emit(event.result)
            finally:
                self._cleanup_workers()
                self._process_events()

    def _handle_worker_error(self, event: WorkerErrorEvent) -> None:
        with QMutexLocker(self._mutex):
            try:
                self.worker_error.emit(event.error)
            finally:
                self._cleanup_workers()
                self._process_events()

    def _cleanup_workers(self) -> None:
        with QMutexLocker(self._mutex):
            for worker in self.active_workers[:]:
                try:
                    if hasattr(worker.signals, "cleanup"):
                        worker.signals.cleanup.emit()
                    if hasattr(worker.signals, "finished"):
                        worker.signals.finished.disconnect()
                    if hasattr(worker.signals, "error"):
                        worker.signals.error.disconnect()
                except (TypeError, RuntimeError):
                    pass
                finally:
                    try:
                        self.active_workers.remove(worker)
                    except ValueError:
                        pass
            QTimer.singleShot(0, self._process_events)

    def cleanup_thread(self) -> None:
        logger.debug("Starting ThreadController cleanup process")
        try:
            with QMutexLocker(self._mutex):
                for worker in self.active_workers:
                    if hasattr(worker.signals, "cleanup"):
                        worker.signals.cleanup.emit()

                self._cleanup_workers()
                self.threadpool.clear()

                MAX_WAIT_MS = 1000
                WAIT_INTERVAL_MS = 100
                total_waited = 0

                while not self.threadpool.waitForDone(WAIT_INTERVAL_MS):
                    total_waited += WAIT_INTERVAL_MS
                    if total_waited >= MAX_WAIT_MS:
                        logger.warning(
                            f"Thread pool cleanup timed out after {MAX_WAIT_MS}ms"
                        )
                        break
                    self._process_events()

                self.cleanup_complete.emit()

        except Exception as e:
            logger.error(f"Error during thread cleanup: {str(e)}")
        finally:
            logger.debug("ThreadController cleanup process completed")

    def __del__(self) -> None:
        logger.debug("ThreadController destructor called")
        try:
            self.cleanup_thread()
        except Exception as e:
            logger.error(f"Error during ThreadController destruction: {str(e)}")
