"""
GynTree: ThreadController manages the lifecycle of worker threads.
This controller is responsible for handling background tasks like auto-exclusion
analysis, ensuring the UI remains responsive. It manages starting, stopping,
and cleaning up QThreads and their associated workers.

Responsibilities:
- Start worker threads for long-running tasks (e.g., auto-exclusion).
- Handle thread cleanup and error handling.
- Ensure proper communication between threads and the main UI.
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QThreadPool, QRunnable, pyqtSlot, QTimer
from controllers.AutoExcludeWorker import AutoExcludeWorker

logger = logging.getLogger(__name__)

class WorkerSignals(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

class AutoExcludeWorkerRunnable(QRunnable):
    def __init__(self, project_context):
        super().__init__()
        self.worker = AutoExcludeWorker(project_context)
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.worker.run()
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))

class ThreadController(QObject):
    worker_finished = pyqtSignal(list)
    worker_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        self.active_workers = []
        logger.debug(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

    def start_auto_exclude_thread(self, project_context):
        self.cleanup_thread()  # Ensure previous threads are cleaned up
        worker = AutoExcludeWorkerRunnable(project_context)
        worker.signals.finished.connect(self.worker_finished.emit)
        worker.signals.error.connect(self.worker_error.emit)
        self.active_workers.append(worker)
        self.threadpool.start(worker)

    def cleanup_thread(self):
        logger.debug("Starting ThreadController cleanup process")
        try:
            # Clear the thread pool
            self.threadpool.clear()

            # Disconnect signals and clear active workers
            for worker in self.active_workers:
                if hasattr(worker, 'signals'):
                    worker.signals.finished.disconnect()
                    worker.signals.error.disconnect()
            self.active_workers.clear()

            # Wait for all threads to finish
            if not self.threadpool.waitForDone(5000):  # 5 seconds timeout
                logger.warning("ThreadPool did not finish in time. Some threads may still be running.")

        except RuntimeError as e:
            logger.error(f"Error during thread cleanup: {str(e)}")
        
        logger.debug("ThreadController cleanup process completed")

    def __del__(self):
        logger.debug("ThreadController destructor called")
        try:
            self.cleanup_thread()
        except Exception as e:
            logger.error(f"Error in ThreadController destruction: {str(e)}")