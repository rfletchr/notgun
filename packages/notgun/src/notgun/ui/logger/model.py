import logging
from qtpy import QtCore, QtGui, QtWidgets

ItemDataRole = QtCore.Qt.ItemDataRole


class LogRecordModel(QtCore.QAbstractTableModel):
    """A Qt model that holds LogRecords."""

    def __init__(self, max_records: int = 1000, parent=None):
        super().__init__(parent)
        self.records: list[logging.LogRecord] = []
        self.max_records = max_records
        self.debug_icon = QtGui.QIcon.fromTheme("system-run")
        self.info_icon = QtGui.QIcon.fromTheme("dialog-information")
        self.warning_icon = QtGui.QIcon.fromTheme("dialog-warning")
        self.error_icon = QtGui.QIcon.fromTheme("dialog-error")

        self.debug_bg_color = QtGui.QColor(220, 240, 220, 16)
        self.info_bg_color = QtGui.QColor(0, 255, 200, 16)
        self.warning_bg_color = QtGui.QColor(255, 255, 0, 16)
        self.error_bg_color = QtGui.QColor(255, 0, 0, 16)

    def headerData(self, section, orientation, /, role=...):
        if role != ItemDataRole.DisplayRole:
            return

        if orientation == QtCore.Qt.Orientation.Horizontal:
            if section == 0:
                return "Level"
            elif section == 1:
                return "Message"

        return

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self.records)

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        return 2

    def data(self, index: QtCore.QModelIndex, role: int = ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.records)):
            return

        record = self.records[index.row()]
        if index.column() == 0:
            if role == ItemDataRole.DecorationRole:
                if record.levelno >= logging.ERROR:
                    return self.error_icon
                elif record.levelno >= logging.WARNING:
                    return self.warning_icon
                elif record.levelno >= logging.INFO:
                    return self.info_icon
                elif record.levelno >= logging.DEBUG:
                    return self.debug_icon
                else:
                    return
            elif role == ItemDataRole.DisplayRole:
                return record.levelname

        elif index.column() == 1 and role == ItemDataRole.DisplayRole:
            return record.getMessage()

        elif role == ItemDataRole.BackgroundRole:
            if record.levelno >= logging.ERROR:
                return self.error_bg_color
            elif record.levelno >= logging.WARNING:
                return self.warning_bg_color
            elif record.levelno >= logging.INFO:
                return self.info_bg_color
            elif record.levelno >= logging.DEBUG:
                return self.debug_bg_color

        return

    def add_record(self, record: logging.LogRecord) -> None:
        self.beginInsertRows(QtCore.QModelIndex(), len(self.records), len(self.records))
        self.records.append(record)
        if len(self.records) > self.max_records:
            self.records.pop(0)
            self.beginRemoveRows(QtCore.QModelIndex(), 0, 0)
            self.endRemoveRows()
        self.endInsertRows()
