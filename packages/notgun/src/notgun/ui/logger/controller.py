import logging
import queue

import notgun.ui.logger.model
import notgun.ui.logger.view

from qtpy import QtCore


class QueueHandler(logging.Handler):
    """Logging handler that pushes LogRecords into a queue."""

    def __init__(self, log_queue: queue.Queue) -> None:
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        self.log_queue.put_nowait(record)


class LogController(QtCore.QObject):
    """Controller that manages logging from a queue to a model."""

    def __init__(self, view: notgun.ui.logger.view.LogView | None = None, parent=None):
        super().__init__(parent)
        self.log_queue: queue.Queue[logging.LogRecord] = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        self.model = notgun.ui.logger.model.LogRecordModel()

        self.view = view or notgun.ui.logger.view.LogView()
        self.view.setModel(self.model)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)  # Check the queue every 100 ms
        self.timer.timeout.connect(self.processQueue)
        self.timer.start()
        self._loggers: list[logging.Logger] = []

    def processQueue(self) -> None:
        """Process all LogRecords in the queue."""
        while not self.log_queue.empty():
            try:
                record = self.log_queue.get_nowait()
                self.model.add_record(record)
            except queue.Empty:
                break

    def attachToLogger(self, logger: logging.Logger) -> None:
        """Attach the queue handler to a logger."""
        if logger not in self._loggers:
            logger.addHandler(self.queue_handler)
            self._loggers.append(logger)

    def detachFromLogger(self, logger: logging.Logger) -> None:
        """Detach the queue handler from a logger."""
        if logger in self._loggers:
            logger.removeHandler(self.queue_handler)
            self._loggers.remove(logger)

    def shutdown(self) -> None:
        """Stop the timer and detach from all loggers."""
        self.timer.stop()
        for logger in self._loggers:
            logger.removeHandler(self.queue_handler)
        self._loggers.clear()
