import logging

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

logger = logging.getLogger(__name__)


class WorkerFinishedEvent(QEvent):
    EventType = QEvent.Type(QEvent.User + 1)

    def __init__(self, result):
        super().__init__(WorkerFinishedEvent.EventType)
        self.result = result


class WorkerErrorEvent(QEvent):
    EventType = QEvent.Type(QEvent.User + 2)

    def __init__(self, error):
        super().__init__(WorkerErrorEvent.EventType)
        self.error = error


class WorkerSignals(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    cleanup = pyqtSignal()  # New signal for cleanup


class AutoExcludeWorkerRunnable(QRunnable):
    def __init__(self, project_context):
        super().__init__()
        self.setAutoDelete(True)
        self._priority = QThread.NormalPriority
        if project_context is None:
            raise ValueError("Project context cannot be None")

        self.worker = AutoExcludeWorker(project_context)
        self.signals = WorkerSignals()
        self._is_running = False
        self._stop_requested = False

        # Connect signals using direct connection for thread safety
        self.worker.finished.connect(self._handle_worker_finished, Qt.DirectConnection)
        self.worker.error.connect(self._handle_worker_error, Qt.DirectConnection)
        self.signals.cleanup.connect(self.cleanup, Qt.DirectConnection)

    def cleanup(self):
        """Handle cleanup request"""
        self._stop_requested = True
        self._is_running = False
        self._process_events()

    def priority(self):
        return self._priority

    def setPriority(self, priority):
        self._priority = priority

    def _handle_worker_finished(self, result):
        if not self._stop_requested:
            if isinstance(result, str):
                self.signals.finished.emit([result])
            elif isinstance(result, list):
                self.signals.finished.emit(result)
            else:
                self.signals.finished.emit([str(result)] if result is not None else [])

        self._is_running = False
        QTimer.singleShot(0, self._process_events)

    def _handle_worker_error(self, error):
        if not self._stop_requested:
            self.signals.error.emit(str(error))  # Ensure raw error message

        self._is_running = False
        QTimer.singleShot(0, self._process_events)

    def _process_events(self):
        QCoreApplication.processEvents()

    @pyqtSlot()
    def run(self):
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
    cleanup_complete = pyqtSignal()  # New signal for cleanup completion

    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        self.active_workers = []
        self._mutex = QMutex(QMutex.Recursive)  # Changed to recursive mutex
        self.moveToThread(QCoreApplication.instance().thread())
        QTimer.singleShot(0, self._process_events)
        logger.debug(
            f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads"
        )

    def start_auto_exclude_thread(self, project_context):
        if not project_context:
            logger.error("Cannot start thread with None project context")
            return None

        try:
            worker = AutoExcludeWorkerRunnable(project_context)

            def finished_handler(result):
                with QMutexLocker(self._mutex):
                    event = WorkerFinishedEvent(result)
                    QCoreApplication.instance().postEvent(
                        self, event, Qt.HighEventPriority
                    )
                    QTimer.singleShot(0, self._process_events)

            def error_handler(error):
                with QMutexLocker(self._mutex):
                    event = WorkerErrorEvent(error)
                    QCoreApplication.instance().postEvent(
                        self, event, Qt.HighEventPriority
                    )
                    QTimer.singleShot(0, self._process_events)

            worker.signals.finished.connect(finished_handler, Qt.QueuedConnection)
            worker.signals.error.connect(error_handler, Qt.QueuedConnection)

            with QMutexLocker(self._mutex):
                self.active_workers.append(worker)
                self.threadpool.start(worker)
                QTimer.singleShot(0, self._process_events)

            return worker

        except Exception as e:
            logger.error(f"Error creating worker: {str(e)}")
            return None

    def _process_events(self):
        if QThread.currentThread() == QCoreApplication.instance().thread():
            QCoreApplication.processEvents()

    def event(self, event):
        if event.type() == WorkerFinishedEvent.EventType:
            self._handle_worker_finished(event)
            return True
        elif event.type() == WorkerErrorEvent.EventType:
            self._handle_worker_error(event)
            return True
        return super().event(event)

    def _handle_worker_finished(self, event):
        with QMutexLocker(self._mutex):
            try:
                self.worker_finished.emit(event.result)
            finally:
                self._cleanup_workers()
                self._process_events()

    def _handle_worker_error(self, event):
        with QMutexLocker(self._mutex):
            try:
                self.worker_error.emit(event.error)
            finally:
                self._cleanup_workers()
                self._process_events()

    def _cleanup_workers(self):
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

    def cleanup_thread(self):
        """Clean up thread resources properly"""
        logger.debug("Starting ThreadController cleanup process")
        try:
            with QMutexLocker(self._mutex):
                # Signal all workers to stop
                for worker in self.active_workers:
                    if hasattr(worker.signals, "cleanup"):
                        worker.signals.cleanup.emit()

                self._cleanup_workers()
                self.threadpool.clear()

                # Wait for thread pool with timeout
                MAX_WAIT_MS = 1000  # 1 second timeout
                WAIT_INTERVAL_MS = 100  # Check every 100ms
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

    def __del__(self):
        logger.debug("ThreadController destructor called")
        try:
            self.cleanup_thread()
        except Exception as e:
            logger.error(f"Error during ThreadController destruction: {str(e)}")
