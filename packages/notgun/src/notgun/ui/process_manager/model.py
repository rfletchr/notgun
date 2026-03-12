import enum
import time
from qtpy import QtCore, QtGui

import notgun.launcher


class ModelRoles(enum.IntEnum):
    ProcessInfo = QtCore.Qt.ItemDataRole.UserRole
    Timestamp = QtCore.Qt.ItemDataRole.UserRole + 1
    ProcessId = QtCore.Qt.ItemDataRole.UserRole + 2


class ProcessInfoListModel(QtGui.QStandardItemModel):
    """
    Model for displaying a list of launched processes and their statuses.

    Processes store their state in the log directory, and this model scans
    the directory to find them and display their status.
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setHorizontalHeaderLabels(["Launched At", "Name"])

    def scan(self, log_directory: str):

        pid_to_item = {}
        for row in range(self.rowCount()):
            item = self.item(row, 1)
            process_id = item.data(ModelRoles.ProcessId)
            pid_to_item[process_id] = item

        items = tuple(notgun.launcher.ProcessInfo.iter(log_directory))

        for process_info in items:
            if process_info.pid in pid_to_item:
                item = pid_to_item[process_info.pid]
            else:
                item = QtGui.QStandardItem(process_info.label)

                timestamp_str = time.strftime(
                    "%Y-%m-%d %H:%M", time.localtime(process_info.timestamp)
                )
                ts_item = QtGui.QStandardItem(timestamp_str)
                self.appendRow([ts_item, item])

            item.setData(process_info, ModelRoles.ProcessInfo)
            item.setData(process_info.timestamp, ModelRoles.Timestamp)
            item.setData(process_info.pid, ModelRoles.ProcessId)

            date_item = self.item(item.row(), 0)

            if process_info.return_code is not None:
                if process_info.return_code == 0:
                    fg = QtGui.QBrush(QtGui.QColor("green"))
                else:
                    fg = QtGui.QBrush(QtGui.QColor("red"))
                item.setForeground(fg)
                date_item.setForeground(fg)
